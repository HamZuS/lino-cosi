# -*- coding: UTF-8 -*-
# Copyright 2014 Luc Saffre
# This file is part of Lino Cosi.
#
# Lino Cosi is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# Lino Cosi is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License along with Lino Cosi.  If not, see
# <http://www.gnu.org/licenses/>.


"""This defines two functions which convert a Belgian National Bank
Account Number (NBAN) into an (IBAN, BIC) pair.

There are two ways to implement this:

- using a hard-coded mapping of Belgian bank numbers to their BIC code:
  :func:`belgian_nban_to_iban_bic`
- using an online service : :func:`belgian_nban_to_iban_bic_soap`

Usage examples:

>>> belgian_nban_to_iban_bic('340-1549215-66')
('BE07340154921566', 'BBRUBEBB')
>>> belgian_nban_to_iban_bic('001-6012719-56')
('BE20001601271956', 'GEBABEBB')
>>> belgian_nban_to_iban_bic('063-4975581-01')
('BE43063497558101', 'GKCCBEBB')

Here is an invalid Belgian NBAN:

>>> belgian_nban_to_iban_bic("001-1148294-83")  #doctest: +ELLIPSIS
Traceback (most recent call last):
...
ValidationError: [u'Belgian NBAN ends with 83 (expected 84)!']


This is also used by :mod:`lino_cosi.lib.sepa`.


See also:

- http://fr.wikipedia.org/wiki/ISO_13616#Composition
- http://www.europebanks.info/ibanguide.htm#5

"""

# from __future__ import unicode_literals
from __future__ import print_function

import logging
from lino.api import dd, _, rt
from lino_cosi.lib.sepa.camt import CamtParser
import time

logger = logging.getLogger(__name__)

from django.core.exceptions import ValidationError

# try:
#     from django_iban.validators import swift_bic_validator, IBANValidator
# except ImportError:
#     pass

try:
    from suds.client import Client

except ImportError:
    pass

_CLIENT = None


def client():
    global _CLIENT
    if _CLIENT is None:
        url = 'http://www.ibanbic.be/IBANBIC.asmx?WSDL'
        _CLIENT = Client(url)  # Will fail if suds is not installed.
    return _CLIENT


# The following string is taken from
# http://www.nbb.be/pub/09_00_00_00_00/09_06_00_00_00/09_06_02_00_00.htm?l=en
BANK_CODES = """\
000	BPOT BE B1
001	GEBA BE BB
002	GEBA BE BB
003	GEBA BE BB
004	GEBA BE BB
005	GEBA BE BB
006	GEBA BE BB
007	GEBA BE BB
008	GEBA BE BB
009	GEBA BE BB
010	GEBA BE BB
011	GEBA BE BB
012	GEBA BE BB
013	GEBA BE BB
014	GEBA BE BB
015	GEBA BE BB
016	GEBA BE BB
017	GEBA BE BB
018	GEBA BE BB
019	GEBA BE BB
020	GEBA BE BB
021	GEBA BE BB
022	GEBA BE BB
023	GEBA BE BB
024	GEBA BE BB
025	GEBA BE BB
026	GEBA BE BB
027	GEBA BE BB
028	GEBA BE BB
029	GEBA BE BB
030	GEBA BE BB
031	GEBA BE BB
032	GEBA BE BB
033	GEBA BE BB
034	GEBA BE BB
035	GEBA BE BB
036	GEBA BE BB
037	GEBA BE BB
038	GEBA BE BB
039	GEBA BE BB
040	GEBA BE BB
041	GEBA BE BB
042	GEBA BE BB
043	GEBA BE BB
044	GEBA BE BB
045	GEBA BE BB
046	GEBA BE BB
047	GEBA BE BB
048	GEBA BE BB
049	GEBA BE BB
050	GKCC BE BB
051	GKCC BE BB
052	GKCC BE BB
053	GKCC BE BB
054	GKCC BE BB
055	GKCC BE BB
056	GKCC BE BB
057	GKCC BE BB
058	GKCC BE BB
059	GKCC BE BB
060	GKCC BE BB
061	GKCC BE BB
062	GKCC BE BB
063	GKCC BE BB
064	GKCC BE BB
065	GKCC BE BB
066	GKCC BE BB
067	GKCC BE BB
068	GKCC BE BB
069	GKCC BE BB
070	GKCC BE BB
071	GKCC BE BB
072	GKCC BE BB
073	GKCC BE BB
074	GKCC BE BB
075	GKCC BE BB
076	GKCC BE BB
077	GKCC BE BB
078	GKCC BE BB
079	GKCC BE BB
080	GKCC BE BB
081	GKCC BE BB
082	GKCC BE BB
083	GKCC BE BB
084	GKCC BE BB
085	GKCC BE BB
086	GKCC BE BB
087	GKCC BE BB
088	GKCC BE BB
089	GKCC BE BB
090	GKCC BE BB
091	GKCC BE BB
092	GKCC BE BB
093	GKCC BE BB
094	GKCC BE BB
095	GKCC BE BB
096	GKCC BE BB
097	GKCC BE BB
098	GKCC BE BB
099	GKCC BE BB
100	NBBE BE BB 203
101	NBBE BE BB 203
103	NICA BE BB
104	NICA BE BB
105	NICA BE BB
106	NICA BE BB
107	NICA BE BB
108	NICA BE BB
109	BKCP BE B1 BKB
110	BKCP BE BB
111	ABER BE 21
113	BKCP BE B1 BKB
114	BKCP BE B1 BKB
119	BKCP BE B1 BKB
120	BKCP BE B1 BKB
121	BKCP BE B1 BKB
122	OBKB BE 99
123	OBKB BE 99
124	BKCP BE B1 BKB
125	CPHB BE 75
126	CPHB BE 75
127	BKCP BE B1 BKB
129	BKCP BE B1 BKB
131	BKCP BE B1 BKB
132	BNAG BE BB
133	BKCP BE B1 BKB
134	BKCP BE B1 BKB
137	GEBA BE BB
140	GEBA BE BB
141	GEBA BE BB
142	GEBA BE BB
143	GEBA BE BB
144	GEBA BE BB
145	GEBA BE BB
146	GEBA BE BB
147	GEBA BE BB
148	GEBA BE BB
149	GEBA BE BB
150	BCMC BE BB
171	CPHB BE 75
172	RABO BE 22
173	RABO BE 23
176	BSCH BE BR
177	BSCH BE BR
178	COBA BE BX
179	COBA BE BX
183	BARB BE BB
185	HBKA BE 22
189	SMBC BE BB
190	CREG BE BB
191	CREG BE BB
192	CREG BE BB
193	CREG BE BB
194	CREG BE BB
195	CREG BE BB
196	CREG BE BB
197	CREG BE BB
198	CREG BE BB
199	CREG BE BB
200	GEBA BE BB
201	GEBA BE BB
202	GEBA BE BB
203	GEBA BE BB
204	GEBA BE BB
205	GEBA BE BB
206	GEBA BE BB
207	GEBA BE BB
208	GEBA BE BB
209	GEBA BE BB
210	GEBA BE BB
211	GEBA BE BB
212	GEBA BE BB
213	GEBA BE BB
214	GEBA BE BB
220	GEBA BE BB
221	GEBA BE BB
222	GEBA BE BB
223	GEBA BE BB
224	GEBA BE BB
225	GEBA BE BB
226	GEBA BE BB
227	GEBA BE BB
228	GEBA BE BB
229	GEBA BE BB
230	GEBA BE BB
231	GEBA BE BB
232	GEBA BE BB
233	GEBA BE BB
234	GEBA BE BB
235	GEBA BE BB
236	GEBA BE BB
237	GEBA BE BB
238	GEBA BE BB
239	GEBA BE BB
240	GEBA BE BB
241	GEBA BE BB
242	GEBA BE BB
243	GEBA BE BB
244	GEBA BE BB
245	GEBA BE BB
246	GEBA BE BB
247	GEBA BE BB
248	GEBA BE BB
249	GEBA BE BB
250	GEBA BE BB
251	GEBA BE BB
257	GEBA BE BB
259	GEBA BE BB
260	GEBA BE BB
261	GEBA BE BB
262	GEBA BE BB
263	GEBA BE BB
264	GEBA BE BB
265	GEBA BE BB
266	GEBA BE BB
267	GEBA BE BB
268	GEBA BE BB
269	GEBA BE BB
270	GEBA BE BB
271	GEBA BE BB
272	GEBA BE BB
273	GEBA BE BB
274	GEBA BE BB
275	GEBA BE BB
276	GEBA BE BB
277	GEBA BE BB
278	GEBA BE BB
279	GEBA BE BB
280	GEBA BE BB
281	GEBA BE BB
282	GEBA BE BB
283	GEBA BE BB
284	GEBA BE BB
285	GEBA BE BB
286	GEBA BE BB
287	GEBA BE BB
288	GEBA BE BB
289	GEBA BE BB
290	GEBA BE BB
291	GEBA BE BB
292	GEBA BE BB
293	GEBA BE BB
294	GEBA BE BB
295	GEBA BE BB
296	GEBA BE BB
297	GEBA BE BB
298	GEBA BE BB
299	BPOT BE B1
300	BBRU BE BB
301	BBRU BE BB
302	BBRU BE BB
303	BBRU BE BB
304	BBRU BE BB
305	BBRU BE BB
306	BBRU BE BB
307	BBRU BE BB
308	BBRU BE BB
309	BBRU BE BB
310	BBRU BE BB
311	BBRU BE BB
312	BBRU BE BB
313	BBRU BE BB
314	BBRU BE BB
315	BBRU BE BB
316	BBRU BE BB
317	BBRU BE BB
318	BBRU BE BB
319	BBRU BE BB
320	BBRU BE BB
321	BBRU BE BB
322	BBRU BE BB
323	BBRU BE BB
324	BBRU BE BB
325	BBRU BE BB
326	BBRU BE BB
327	BBRU BE BB
328	BBRU BE BB
329	BBRU BE BB
330	BBRU BE BB
331	BBRU BE BB
332	BBRU BE BB
333	BBRU BE BB
334	BBRU BE BB
335	BBRU BE BB
336	BBRU BE BB
337	BBRU BE BB
338	BBRU BE BB
339	BBRU BE BB
340	BBRU BE BB
341	BBRU BE BB
342	BBRU BE BB
343	BBRU BE BB
344	BBRU BE BB
345	BBRU BE BB
346	BBRU BE BB
347	BBRU BE BB
348	BBRU BE BB
349	BBRU BE BB
350	BBRU BE BB
351	BBRU BE BB
352	BBRU BE BB
353	BBRU BE BB
354	BBRU BE BB
355	BBRU BE BB
356	BBRU BE BB
357	BBRU BE BB
358	BBRU BE BB
359	BBRU BE BB
360	BBRU BE BB
361	BBRU BE BB
362	BBRU BE BB
363	BBRU BE BB
364	BBRU BE BB
365	BBRU BE BB
366	BBRU BE BB
367	BBRU BE BB
368	BBRU BE BB
369	BBRU BE BB
370	BBRU BE BB
371	BBRU BE BB
372	BBRU BE BB
373	BBRU BE BB
374	BBRU BE BB
375	BBRU BE BB
376	BBRU BE BB
377	BBRU BE BB
378	BBRU BE BB
379	BBRU BE BB
380	BBRU BE BB
381	BBRU BE BB
382	BBRU BE BB
383	BBRU BE BB
384	BBRU BE BB
385	BBRU BE BB
386	BBRU BE BB
387	BBRU BE BB
388	BBRU BE BB
389	BBRU BE BB
390	BBRU BE BB
391	BBRU BE BB
392	BBRU BE BB
393	BBRU BE BB
394	BBRU BE BB
395	BBRU BE BB
396	BBRU BE BB
397	BBRU BE BB
398	BBRU BE BB
399	BBRU BE BB
400	KRED BE BB
401	KRED BE BB
402	KRED BE BB
403	KRED BE BB
404	KRED BE BB
405	KRED BE BB
406	KRED BE BB
407	KRED BE BB
408	KRED BE BB
409	KRED BE BB
410	KRED BE BB
411	KRED BE BB
412	KRED BE BB
413	KRED BE BB
414	KRED BE BB
415	KRED BE BB
416	KRED BE BB
417	KRED BE BB
418	KRED BE BB
419	KRED BE BB
420	KRED BE BB
421	KRED BE BB
422	KRED BE BB
423	KRED BE BB
424	KRED BE BB
425	KRED BE BB
426	KRED BE BB
427	KRED BE BB
428	KRED BE BB
429	KRED BE BB
430	KRED BE BB
431	KRED BE BB
432	KRED BE BB
433	KRED BE BB
434	KRED BE BB
435	KRED BE BB
436	KRED BE BB
437	KRED BE BB
438	KRED BE BB
439	KRED BE BB
440	KRED BE BB
441	KRED BE BB
442	KRED BE BB
443	KRED BE BB
444	KRED BE BB
445	KRED BE BB
446	KRED BE BB
447	KRED BE BB
448	KRED BE BB
449	KRED BE BB
450	KRED BE BB
451	KRED BE BB
452	KRED BE BB
453	KRED BE BB
454	KRED BE BB
455	KRED BE BB
456	KRED BE BB
457	KRED BE BB
458	KRED BE BB
459	KRED BE BB
460	KRED BE BB
461	KRED BE BB
462	KRED BE BB
463	KRED BE BB
464	KRED BE BB
465	KRED BE BB
466	KRED BE BB
467	KRED BE BB
468	KRED BE BB
469	KRED BE BB
470	KRED BE BB
471	KRED BE BB
472	KRED BE BB
473	KRED BE BB
474	KRED BE BB
475	KRED BE BB
476	KRED BE BB
477	KRED BE BB
478	KRED BE BB
479	KRED BE BB
480	KRED BE BB
481	KRED BE BB
482	KRED BE BB
483	KRED BE BB
484	KRED BE BB
485	KRED BE BB
486	KRED BE BB
487	KRED BE BB
488	KRED BE BB
489	KRED BE BB
490	KRED BE BB
491	KRED BE BB
492	KRED BE BB
493	KRED BE BB
494	KRED BE BB
495	KRED BE BB
496	KRED BE BB
497	KRED BE BB
498	KRED BE BB
499	KRED BE BB
501	DHBN BE BB
507	DIER BE 21
508	PARB BE BZ MDC
509	ABNA BE 2A IPC
510	VAPE BE 21
512	DNIB BE 21
513	SGPB BE 99
514	PUIL BE BB
515	IRVT BE BB
517	FORD BE 21
519	BNYM BE BB
521	FVLB BE 22
522	UTWB BE BB
523	TRIO BE BB
524	WAFA BE BB
525	FVLB BE 2E
530	SHIZ BE BB
535	FBHL BE 22
541	BKID BE 22
546	WAFA BE BB
548	LOCY BE BB
549	CHAS BE BX
550	GKCC BE BB
551	GKCC BE BB
552	GKCC BE BB
553	GKCC BE BB
554	GKCC BE BB
555	GKCC BE BB
556	GKCC BE BB
557	GKCC BE BB
558	GKCC BE BB
559	GKCC BE BB
560	GKCC BE BB
561	FTNO BE B1
562	GKCC BE BB
563	GKCC BE BB
564	GKCC BE BB
565	GKCC BE BB
566	GKCC BE BB
567	GKCC BE BB
568	GKCC BE BB
569	GKCC BE BB
570	CITI BE BX
571	CITI BE BX
572	CITI BE BX
573	CITI BE BX
574	CITI BE BX
575	CITI BE BX
576	CITI BE BX
577	CITI BE BX
578	CITI BE BX
579	CITI BE BX
581	MHCB BE BB
583	DEGR BE BB
584	ICIC GB 2L
585	RCBP BE BB
586	CFFR BE B1
587	BIBL BE 21
588	CMCI BE B1
590	BSCH BE BB
591	BSCH BE BB
592	BSCH BE BB
593	BSCH BE BB
594	BSCH BE BB
595	CTBK BE BX
596	CTBK BE BX
597	CTBK BE BX
598	CTBK BE BX
599	CTBK BE BX
600	CTBK BE BX
601	CTBK BE BX
605	BKCH BE BB
607	ICBK BE BB
610	DEUT BE BE
611	DEUT BE BE
612	DEUT BE BE
613	DEUT BE BE
624	GKCC BE BB
625	GKCC BE BB
626	CPBI FRPP
630	BBRU BE BB
631	BBRU BE BB
634	BNAG BE BB
635	BNAG BE BB
636	BNAG BE BB
638	GKCC BE BB
639	ABNA BE 2A MYO
640	ADIA BE 22
642	BBVA BE BB
643	BMPB BE BB
645	JVBA BE 22
646	BNAG BE BB
647	BNAG BE BB
651	KEYT BE BB
652	HBKA BE 22
656	ETHI BE BB
657	GKCC BE BB
658	HABB BE BB
664	BCDM BE BB
665	SPAA BE 22
668	SBIN BE 2X
671	EURB BE 99
672	GKCC BE BB
673	HBKA BE 22
674	ABNA BE 2A IDJ
675	BYBB BE BB
676	DEGR BE BB
678	DELE BE 22
679	PCHQ BE BB
680	GKCC BE BB
682	GKCC BE BB
683	GKCC BE BB
685	BOFA BE 3X
686	BOFA BE 3X
687	MGTC BE BE
688	SGAB BE B2
690	BNPA BE BB
691	FTSB NL 2R
693	BOTK BE BX
694	DEUT BE BE
696	CRLY BE BB
700	AXAB BE 22
701	AXAB BE 22
702	AXAB BE 22
703	AXAB BE 22
704	AXAB BE 22
705	AXAB BE 22
706	AXAB BE 22
707	AXAB BE 22
708	AXAB BE 22
709	AXAB BE 22
719	FTSB BE 22
720	ABNA BE BR
721	ABNA BE BR
722	ABNA BE 2A IPC
723	ABNA BE BR
724	ABNA BE BR
725	KRED BE BB
726	KRED BE BB
727	KRED BE BB
728	CREG BE BB
729	CREG BE BB
730	KRED BE BB
731	KRED BE BB
732	CREG BE BB
733	KRED BE BB
734	KRED BE BB
735	KRED BE BB
736	KRED BE BB
737	KRED BE BB
738	KRED BE BB
739	KRED BE BB
740	KRED BE BB
741	KRED BE BB
742	CREG BE BB
743	KRED BE BB
744	KRED BE BB
745	KRED BE BB
746	KRED BE BB
747	KRED BE BB
748	KRED BE BB
749	KRED BE BB
750	AXAB BE 22
751	AXAB BE 22
752	AXAB BE 22
753	AXAB BE 22
754	AXAB BE 22
755	AXAB BE 22
756	AXAB BE 22
757	AXAB BE 22
758	AXAB BE 22
759	AXAB BE 22
760	AXAB BE 22
761	AXAB BE 22
762	AXAB BE 22
763	AXAB BE 22
764	AXAB BE 22
765	AXAB BE 22
766	AXAB BE 22
767	AXAB BE 22
768	AXAB BE 22
769	AXAB BE 22
770	AXAB BE 22
771	AXAB BE 22
772	AXAB BE 22
773	AXAB BE 22
774	AXAB BE 22
775	GKCC BE BB
776	GKCC BE BB
777	GKCC BE BB
778	GKCC BE BB
779	GKCC BE BB
780	GKCC BE BB
781	GKCC BE BB
782	GKCC BE BB
783	GKCC BE BB
784	GKCC BE BB
785	GKCC BE BB
786	GKCC BE BB
787	GKCC BE BB
788	GKCC BE BB
789	GKCC BE BB
790	GKCC BE BB
791	GKCC BE BB
792	GKCC BE BB
793	GKCC BE BB
794	GKCC BE BB
795	GKCC BE BB
796	GKCC BE BB
797	GKCC BE BB
798	GKCC BE BB
799	GKCC BE BB
800	AXAB BE 22
801	AXAB BE 22
802	AXAB BE 22
803	AXAB BE 22
804	AXAB BE 22
805	AXAB BE 22
806	AXAB BE 22
807	AXAB BE 22
808	AXAB BE 22
809	AXAB BE 22
810	AXAB BE 22
811	AXAB BE 22
812	AXAB BE 22
813	AXAB BE 22
814	AXAB BE 22
815	AXAB BE 22
816	AXAB BE 22
823	BLUX BE 41
825	DEUT BE BE
826	DEUT BE BE
827	ETHI BE BB
828	HBKA BE 22
829	BMEC BE B1
830	GKCC BE BB
831	GKCC BE BB
832	GKCC BE BB
833	GKCC BE BB
834	GKCC BE BB
835	GKCC BE BB
836	GKCC BE BB
837	GKCC BE BB
838	GKCC BE BB
839	GKCC BE BB
840	PRIB BE BB
841	COVE BE 71
842	UBSW BE BB
843	FTNO BE B1
844	RABO BE 22
845	DEGR BE BB
850	SPAA BE 22
851	SPAA BE 22
852	SPAA BE 22
853	SPAA BE 22
859	SPAA BE 22
860	SPAA BE 22
861	SPAA BE 22
862	SPAA BE 22
863	SPAA BE 22
865	SPAA BE 22
866	SPAA BE 22
868	KRED BE BB
870	BNAG BE BB
871	BNAG BE BB
872	BNAG BE BB
873	PCHQ BE BB
874	BNAG BE BB
876	MBWM BE BB
877	BNAG BE BB
878	BNAG BE BB
879	BNAG BE BB
880	HBKA BE 22
881	HBKA BE 22
882	HBKA BE 22
883	HBKA BE 22
884	HBKA BE 22
885	HBKA BE 22
886	HBKA BE 22
887	HBKA BE 22
888	HBKA BE 22
889	HBKA BE 22
890	VDSP BE 91
891	VDSP BE 91
892	VDSP BE 91
893	VDSP BE 91
894	VDSP BE 91
895	VDSP BE 91
896	VDSP BE 91
897	VDSP BE 91
898	VDSP BE 91
899	VDSP BE 91
906	CEKV BE 81
907	SPAA BE 22
908	CEKV BE 81
909	FTNO BE B1
910	HBKA BE 22
911	TUNZ BE B1
913	EPBF BE BB
918	BILL BE BB
920	HBKA BE 22
921	HBKA BE 22
922	HBKA BE 22
923	HBKA BE 22
925	HBKA BE 22
929	HBKA BE 22
930	HBKA BE 22
931	HBKA BE 22
932	HBKA BE 22
933	HBKA BE 22
934	HBKA BE 22
935	HBKA BE 22
936	HBKA BE 22
937	HBKA BE 22
938	HBKA BE 22
939	HBKA BE 22
940	CLIQ BE B1
941	CVMC BE BB
942	PUIL BE BB
945	JPMG BE BB
947	AARB BE B1
949	HSBC BE BB
950	CTBK BE BX
951	CTBK BE BX
952	CTBK BE BX
953	CTBK BE BX
954	CTBK BE BX
955	CTBK BE BX
956	CTBK BE BX
957	CTBK BE BX
958	CTBK BE BX
959	CTBK BE BX
960	ABNA BE 2A IPC
961	HBKA BE 22
962	ETHI BE BB
963	AXAB BE 22
965	ETHI BE BB
968	ENIB BE BB
969	PUIL BE BB
970	HBKA BE 22
971	HBKA BE 22
973	ARSP BE 22
975	AXAB BE 22
976	HBKA BE 22
978	ARSP BE 22
979	ARSP BE 22
980	ARSP BE 22
981	PCHQ BE BB
982	PCHQ BE BB
983	PCHQ BE BB
984	PCHQ BE BB
985	BPOT BE B1
986	BPOT BE B1
987	BPOT BE B1
988	BPOT BE B1
"""

# BELGIAN_BICS = {'001': 'GEBABEBB'}
BELGIAN_BICS = {}
for ln in BANK_CODES.splitlines():
    a = ln.split('\t')
    assert len(a) == 2
    bic = a[1].replace(' ', '')
    assert len(bic) in (8, 11)
    BELGIAN_BICS[a[0]] = bic


def be2iban(nban):
    """
    Convert Belgian NBAN to an IBAN.

    Usage examples:

    >>> be2iban("001-1148294-84")
    'BE03001114829484'

    Based on my previous Clipper implementation for TIM:
    http://code.google.com/p/tim/source/browse/SRC/TIMDATA2.PRG

    """
    nban = nban.replace(' ', '')
    nban = nban.replace('-', '')
    if len(nban) != 12:
        raise ValidationError("Length of Belgian NBAN must be 12!")
    m = int(nban[:10]) % 97
    end = nban[-2:]
    if m == 0:
        if end != '97':
            raise ValidationError(
                "Belgian NBAN ends with %s (expected 97)!" % end)
    else:
        if int(end) != m:
            raise ValidationError(
                "Belgian NBAN ends with %s (expected %s)!" % (end, m))
    data = nban + "1114"  # "BE" converted to numbers
    data += "00"  # the yet unknown control digits
    s = "%02d" % (98 - (int(data) % 97))
    return "BE" + s + nban


def iban2bic(iban):
    """
    Return the BIC corresponding to the given Belgian NBAN.

    This is based on a hard-coded mapping.

    Usage examples:

    >>> iban2bic('BE03001114829484')
    'GEBABEBB'

    Based on my previous Clipper implementation for TIM:
    http://code.google.com/p/tim/source/browse/SRC/TIMDATA2.PRG

    """
    iban = iban.replace(' ', '')
    if iban.startswith('BE'):
        k = iban[4:7]
        return BELGIAN_BICS.get(k)


def belgian_nban_to_iban_bic(s):
    """Convert a Belgian National Bank Account Number (NBAN)
into an IBAN, BIC pair.

    """
    iban = be2iban(s)
    # IBANValidator(iban)
    bic = iban2bic(iban)
    # swift_bic_validator(bic)
    return (iban, bic)


def belgian_nban_to_iban_bic_soap(s):
    """Convert a Belgian National Bank Account Number (NBAN) into an IBAN,
BIC pair.

This method uses the free public SOAP service available at `ibanbic.be
<http://www.ibanbic.be/IBANBIC.asmx?op=BBANtoIBANandBIC>`_ and thus
requires Internet access, is slower, but has the advantage of being
more reliable because maintained by `an expert <http://www.ebcs.be>`_.

    """
    s = client().service.BBANtoIBANandBIC(s)
    return s.split('#')


def import_sepa_file(filename, ar=None):
    """Import the filename as an CAMT053 XML file.

    :param filename: file path to get imported :Type :`str`
    :param ar: the Action Request :class:`ActionRequest`
    :return: False if the import catch an error ,otherwise True
    """
    Account = rt.modules.sepa.Account
    Statement = rt.modules.sepa.Statement
    Movement = rt.modules.sepa.Movement

    msg = "File {0} would have imported.".format(filename)
    """Parse a CAMT053 XML file."""
    parser = CamtParser()
    data_file = open(filename, 'rb').read()
    try:
        dd.logger.info("Try parsing with camt.")
        res = parser.parse(data_file)
        if res is not None:
            for _statement in res:
                _iban = _statement.get('account_number', None)
                if _iban is not None:
                    account = Account.objects.filter(iban=_iban)
                    if account:
                        s = Statement(account=account,
                                      date=_statement['date'].strftime("%Y-%m-%d"),
                                      date_done=time.strftime("%Y-%m-%d"),
                                      statement_number=_statement['name'],
                                      balance_end=_statement['balance_end'],
                                      balance_start=_statement['balance_start'],
                                      balance_end_real=_statement['balance_end_real'],
                                      currency_code=_statement['currency_code'])
                        s.save()
                        for _movement in _statement['transactions']:
                            if not Movement.objects.filter(unique_import_id=_movement['unique_import_id']).exists():
                                _ref = _movement.get('ref', '') or ' '
                                m = Movement(statement=s,
                                             unique_import_id=_movement['unique_import_id'],
                                             movement_date=_movement['date'],
                                             amount=_movement['amount'],
                                             partner_name=_movement['partner_name'],
                                             ref=_ref,
                                             bank_account=account)
                                m.save()

    except ValueError:
        dd.logger.info("Statement file was not a camt file.")
        return False
    dd.logger.info(msg)
    if ar is not None:
        ar.info(msg)
    return True


def _test():
    import doctest
    doctest.testmod()


if __name__ == "__main__":
    _test()
