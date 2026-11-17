# Translation catalogues

The eleven locale directories (`ca`, `en`, `en_GB`, `en_IN`, `en_US`, `es_419`, `es_ES`, `eu`, `gl`, `pt_BR`, `pt_PT`) are the Django gettext catalogues for Olokuti Digital.

## Updating and compiling

On environments with GNU gettext tools installed, run `django-admin makemessages -a` to extract updated `msgid` entries and `django-admin compilemessages` to rebuild binary `.mo` files.

On developer environments without GNU `msgfmt`, run:

```bash
python manage.py compile_locales
```

This management command calls `compilemessages` when GNU gettext is available and falls back to a built-in pure-Python GNU `.mo` compiler when `msgfmt` is not on `PATH`. Keep both `.po` source files and compiled `.mo` files committed.

Product originals and their optional `ProductTranslation` records are stored separately. Selecting an interface language never overwrites source product content.
