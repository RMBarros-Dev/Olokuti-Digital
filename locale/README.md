# Translation catalogues

The ten locale directories are the Django gettext catalogues for this prototype. Their `.po` and `.mo` files currently contain headers only: interface strings still fall back to their English source text. The compiled headers let Django recognize each configured language prefix; they do not provide translations. No catalogue is represented as reviewed or complete. A qualified reviewer should translate the extracted `msgid` values, check regional conventions, and then recompile the catalogues before release.

Use `django-admin makemessages -a` to extract interface strings after installing the development requirements and GNU gettext tools. Review every `.po` file, then run `django-admin compilemessages` to create the corresponding `.mo` files. Keep both the `.po` sources and compiled `.mo` files available to the runtime.

Product originals and their optional `ProductTranslation` records are stored separately. Selecting an interface language never overwrites source product content.
