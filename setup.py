from setuptools import setup
fn = 'lino_cosi/setup_info.py'
exec(compile(open(fn, "rb").read(), fn, 'exec'))
# above line is equivalent to the line below, except that it works
# also in Python 3:
# execfile(fn)
if __name__ == '__main__':
    setup(**SETUP_INFO)
