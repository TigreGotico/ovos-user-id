from setuptools import setup

UTTERANCE_ENTRY_POINT = f'ovos-user-auth-phrase=ovos_user_id.opm:UserAuthPhrasePlugin'
METADATA_ENTRY_POINT = (
    'ovos-user-session-manager=ovos_user_id.opm:UserSessionPlugin',
    'ovos-user-face-auth=ovos_user_id.opm:UserFaceAuthPlugin'
)

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
        'neon.plugin.text': UTTERANCE_ENTRY_POINT,
        'neon.plugin.metadata': METADATA_ENTRY_POINT,
        'console_scripts': [
            'ovos-user-manager=ovos_user_id.tui:cli'
        ]
    }
)
