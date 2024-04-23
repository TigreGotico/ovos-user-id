from setuptools import setup

METADATA_ENTRY_POINT = 'ovos-user-session-manager=ovos_user_id:UserSessionPlugin'


setup(
    name='ovos-user-id',
    version='0.0.0a1',
    packages=['ovos_user_id'],
    url='',
    license='',
    author='jarbasAi',
    author_email='jarbasai@mailfence.com',
    description='',
    entry_points={
        'neon.plugin.metadata': METADATA_ENTRY_POINT,
        'console_scripts': [
            'ovos-user-manager=ovos_user_id.tui:cli'
        ]
    }
)
