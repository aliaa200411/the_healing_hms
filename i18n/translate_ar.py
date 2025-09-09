import polib
from googletrans import Translator

translator = Translator()

po = polib.pofile('/home/lama/odoo/custom_addons/the_healing_hms_new/the_healing_hms/i18n/ar.po')

for entry in po:
    if not entry.msgstr: 
        translated = translator.translate(entry.msgid, src='en', dest='ar')
        entry.msgstr = translated.text

po.save('/home/lama/odoo/custom_addons/the_healing_hms_new/the_healing_hms/i18n/ar_translated.po')

