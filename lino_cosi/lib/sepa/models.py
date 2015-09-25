# -*- coding: UTF-8 -*-
# Copyright 2014-2015 Luc Saffre
# License: BSD (see file COPYING for details)

"""
Database models for `lino.modlib.sepa`.

"""

from __future__ import unicode_literals
import logging
from lino_cosi.lib.sepa.camt import CamtParser
import glob
import os
from django.db import models
from lino.api import dd, _
from lino.core.utils import ChangeWatcher
from .fields import IBANField, BICField
from .utils import belgian_nban_to_iban_bic, iban2bic, import_sepa_file

logger = logging.getLogger(__name__)


class ImportStatements(dd.Action):
    """Import the .xml files found in the directory specified at
    :attr:`import_statements_path
    <lino.modlib.sepa.Plugin.import_statements_path>`.

    End-users invoke this via the menu command :menuselection:`SEPA
    --> Import SEPA`.

    When a file has been successfully imported, Lino deletes it.

    It might happen that an .xml file accidentally gets downloaded a
    second time. Lino does not create these statements again.

    """
    label = _("Import SEPA")
    http_method = 'POST'
    select_rows = False

    def get_view_permission(self, profile):
        """Make it invisible when :attr:`import_statements_path
        <lino.modlib.sepa.Plugin.import_statements_path>` is empty.

        """
        if not dd.plugins.sepa.import_statements_path:
            return False
        return super(ImportStatements, self).get_view_permission(profile)

    def run_from_ui(self, ar):
        pth = dd.plugins.sepa.import_statements_path
        wc = os.path.join(pth, '*.xml')
        dd.logger.info("Importing SEPA statements from %s...", wc)
        count = 0
        if pth:
            for filename in glob.iglob(wc):
                import_sepa_file(filename,ar)
                count += 1
            msg = "{0} xml files would have been imported.".format(count)
            dd.logger.info(msg)
            return ar.success(msg, alert=_("Success"))
        msg = "No import_statements_path configured."
        return ar.error(msg, alert=_("Error"))


dd.inject_action('system.SiteConfig', import_sepa=ImportStatements())


class Account(dd.Model):
    """A bank account related to a given :class:`Partner
    <lino.modlib.models.contacts.Partner>`.

    One partner can have more than one bank account.

    """

    class Meta:
        abstract = dd.is_abstract_model(__name__, 'Account')
        verbose_name = _("Account")
        verbose_name_plural = _("Accounts")

    partner = dd.ForeignKey(
        'contacts.Partner',
        related_name='sepa_accounts')

    iban = IBANField(verbose_name=_("IBAN"))
    bic = BICField(verbose_name=_("BIC"), blank=True)

    remark = models.CharField(_("Remark"), max_length=200, blank=True)

    primary = models.BooleanField(
        _("Primary"),
        default=False,
        help_text=_(
            "Enabling this field will automatically disable any "
            "previous primary account and update "
            "the partner's IBAN and BIC"))

    allow_cascaded_delete = ['partner']

    def __unicode__(self):
        if self.remark:
            return "{0} ({1})".format(self.iban, self.remark)
        return self.iban

    def full_clean(self):
        if self.iban and not self.bic:
            if self.iban[0].isdigit():
                iban, bic = belgian_nban_to_iban_bic(self.iban)
                self.bic = bic
                self.iban = iban
            else:
                self.bic = iban2bic(self.iban) or ''
        super(Account, self).full_clean()

    def after_ui_save(self, ar, cw):
        super(Account, self).after_ui_save(ar, cw)
        if self.primary:
            mi = self.partner
            for o in mi.sepa_accounts.exclude(id=self.id):
                if o.primary:
                    o.primary = False
                    o.save()
                    ar.set_response(refresh_all=True)
            watcher = ChangeWatcher(mi)
            for k in PRIMARY_FIELDS:
                setattr(mi, k, getattr(self, k))
            mi.save()
            watcher.send_update(ar.request)


PRIMARY_FIELDS = dd.fields_list(Account, 'iban bic')


class Statement(dd.Model):
    """A bank statement.

    This data is automaticaly imported by :class:`ImportStatements`.

    """

    class Meta:
        abstract = dd.is_abstract_model(__name__, 'Statement')
        verbose_name = _("Statement")
        verbose_name_plural = _("Statements")

    def __unicode__(self):
        if self.account:
            if self.date:
                return "{0} ({1})".format(self.account, self.date)
            else:
                return self.account
        return ''

    account = dd.ForeignKey('sepa.Account')
    date = models.DateField(_('Date'), null=True)
    date_done = models.DateTimeField(_('Import Date'), null=True)
    statement_number = models.CharField(_('Statement number'), null=False, max_length=128)
    balance_start = dd.PriceField(_("Initial amount"), null=True)
    balance_end = dd.PriceField(_("Final amount"), null=True)
    balance_end_real = dd.PriceField(_("Real end balance"), null=True)
    currency_code = models.CharField(_('Currency'), max_length=3)

    # fields like statement_number, date, solde_initial, solde_final


class Movement(dd.Model):
    """A movement within a bank statement.

    This data is automaticaly imported by :class:`ImportStatements`.

    """

    class Meta:
        abstract = dd.is_abstract_model(__name__, 'Movement')
        verbose_name = _("Movement")
        verbose_name_plural = _("Movements")

    statement = dd.ForeignKey('sepa.Statement')
    unique_import_id = models.CharField(_('Unique import ID'), max_length=128)
    # movement_number = models.CharField(_("Ref of Mov"), null=False, max_length=32)
    movement_date = models.DateField(_('Movement date'), null=True)
    amount = dd.PriceField(_('Amount'), null=True)
    partner = models.ForeignKey('contacts.Partner', related_name='sepa_movement', null=True)
    partner_name = models.CharField(_('Partner name'), max_length=35)
    bank_account = dd.ForeignKey('sepa.Account', blank=True, null=True)
    ref = models.CharField(_('Ref'), null=False, max_length=35)


from .ui import *
