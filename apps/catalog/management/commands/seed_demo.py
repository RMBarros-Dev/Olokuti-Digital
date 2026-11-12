from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from apps.accounts.views import ensure_default_role_groups
from apps.audit.services import record_event
from apps.catalog.models import Category, Product, ProductTranslation
from apps.operations.models import OperationalTask


class Command(BaseCommand):
    help = "Create synthetic demonstration records for local development only."

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError("Demo data can only be created when DEBUG=True.")
        self.stdout.write(
            self.style.WARNING(
                "Synthetic demo data only: no origin, certification, supplier, or sustainability "
                "claim is verified."
            )
        )
        ensure_default_role_groups()
        User = get_user_model()
        admin_user = User.objects.filter(is_superuser=True).first()

        categories_data = [
            ("Textiles & Fashion", "Organic cotton and fair-trade garments."),
            ("Home & Living", "Recycled, biodegradable, and zero-waste home goods."),
            ("Natural Care", "Plastic-free personal care and botanical soaps."),
        ]
        categories = {}
        for name, desc in categories_data:
            cat, _ = Category.objects.get_or_create(name=name, defaults={"description": desc})
            categories[name] = cat

        products_data = [
            {
                "name": "Organic Cotton Market Tote",
                "category": categories["Textiles & Fashion"],
                "origin": "Barcelona, Spain",
                "description": "Heavyweight GOTS-certified unbleached organic cotton bag.",
                "sustainability_info": "100% GOTS organic cotton, plastic-free packaging, local cooperative workshop.",
                "translations": {
                    "pt-br": (
                        "Ecobag de Algodão Orgânico",
                        "Sacola resistente de algodão orgânico cru certificado GOTS.",
                        "100% algodão orgânico GOTS, embalagem sem plástico, cooperativa local.",
                    ),
                    "pt-pt": (
                        "Saco de Algodão Biológico",
                        "Saco resistente de algodão biológico cru certificado GOTS.",
                        "100% algodão biológico GOTS, embalagem sem plástico, cooperativa local.",
                    ),
                    "es-es": (
                        "Bolsa de Algodón Orgánico",
                        "Bolsa resistente de algodón orgánico crudo certificado GOTS.",
                        "100% algodón orgánico GOTS, embalaje sin plástico, taller cooperativo local.",
                    ),
                    "es-419": (
                        "Bolsa de Algodón Orgánico",
                        "Bolsa resistente de algodón orgánico crudo certificado GOTS.",
                        "100% algodón orgánico GOTS, empaque libre de plástico, cooperativa local.",
                    ),
                    "ca": (
                        "Bossa de Cotó Orgànic",
                        "Bossa resistent de cotó orgànic cru certificat GOTS.",
                        "100% cotó orgànic GOTS, embalatge sense plàstic, taller cooperatiu local.",
                    ),
                    "gl": (
                        "Bolsa de Algodón Orgánico",
                        "Bolsa resistente de algodón orgánico cru certificado GOTS.",
                        "100% algodón orgánico GOTS, envase sen plástico, cooperativa local.",
                    ),
                    "eu": (
                        "Kotoi Organikozko Poltsa",
                        "GOTS ziurtagiridun kotoi organiko gordineko poltsa erresistentea.",
                        "%100 GOTS kotoi organikoa, plastikorik gabeko bilgarria, tokiko kooperatiba.",
                    ),
                },
            },
            {
                "name": "Recycled Glass Carafe",
                "category": categories["Home & Living"],
                "origin": "Valencia, Spain",
                "description": "Hand-blown carafe crafted from 100% post-consumer recycled glass.",
                "sustainability_info": "100% recycled glass, low-temperature kiln firing, reusable cork stopper.",
                "translations": {
                    "pt-br": (
                        "Jarra de Vidro Reciclado",
                        "Jarra soprada artesanalmente com 100% de vidro reciclado pós-consumo.",
                        "100% vidro reciclado, queima em forno de baixa temperatura, tampa de cortiça.",
                    ),
                    "pt-pt": (
                        "Jarro de Vidro Reciclado",
                        "Jarro soprado artesanalmente com 100% de vidro reciclado pós-consumo.",
                        "100% vidro reciclado, forno de baixa temperatura, rolha de cortiça reutilizável.",
                    ),
                    "es-es": (
                        "Jarra de Vidrio Reciclado",
                        "Jarra soplada artesanalmente con 100% vidrio reciclado posconsumo.",
                        "100% vidrio reciclado, horno de baja temperatura, tapón de corcho.",
                    ),
                    "es-419": (
                        "Jarra de Vidrio Reciclado",
                        "Jarra soplada artesanalmente con 100% vidrio reciclado posconsumo.",
                        "100% vidrio reciclado, horno de baja temperatura, tapón de corcho.",
                    ),
                    "ca": (
                        "Gerra de Vidre Reciclat",
                        "Gerra bufada artesanalment amb 100% vidre reciclat postconsum.",
                        "100% vidre reciclat, forn de baixa temperatura, tap de suro reutilitzable.",
                    ),
                    "gl": (
                        "Xerra de Vidro Reciclado",
                        "Xerra soprada artesanalmente con 100% vidro reciclado posconsumo.",
                        "100% vidro reciclado, forno de baixa temperatura, tapón de cortiza.",
                    ),
                    "eu": (
                        "Beira Birziklatuzko Pitxerra",
                        "Kontsumo osteko %100 beira birziklatuz eskuz puztutako pitxerra.",
                        "%100 beira birziklatua, tenperatura baxuko labea, kortxozko tapoia.",
                    ),
                },
            },
            {
                "name": "Cold-Pressed Olive Oil Soap Bar",
                "category": categories["Natural Care"],
                "origin": "Girona, Spain",
                "description": "Gentle botanical soap bar made with organic extra-virgin olive oil and lavender.",
                "sustainability_info": "Biodegradable formula, zero palm oil, compostable kraft paper wrap.",
                "translations": {
                    "pt-br": (
                        "Sabonete Artesanal de Azeite de Oliva",
                        "Sabonete botânico suave feito com azeite extravirgem orgânico e lavanda.",
                        "Fórmula biodegradável, zero óleo de palma, embalagem de papel kraft compostável.",
                    ),
                    "pt-pt": (
                        "Sabonete Artesanal de Azeite Biológico",
                        "Sabonete botânico suave feito com azeite virgem extra biológico e alfazema.",
                        "Fórmula biodegradável, sem óleo de palma, papel kraft compostável.",
                    ),
                    "es-es": (
                        "Jabón Artesanal de Aceite de Oliva",
                        "Jabón botánico suave elaborado con aceite de oliva virgen extra ecológico y lavanda.",
                        "Fórmula biodegradable, sin aceite de palma, envoltorio de papel kraft compostable.",
                    ),
                    "es-419": (
                        "Jabón Artesanal de Aceite de Oliva",
                        "Jabón botánico suave elaborado con aceite de oliva extra virgen orgánico y lavanda.",
                        "Fórmula biodegradable, libre de aceite de palma, empaque de papel kraft compostable.",
                    ),
                    "ca": (
                        "Sabó Artesanal d'Oli d'Oliva",
                        "Sabó botànic suau elaborat amb oli d'oliva verge extra ecològic i espígol.",
                        "Fórmula biodegradable, sense oli de palma, embolcall de paper kraft compostable.",
                    ),
                    "gl": (
                        "Xabón Artesanal de Aceite de Oliva",
                        "Xabón botánico suave elaborado con aceite de oliva virxe extra ecolóxico e lavanda.",
                        "Fórmula biodegradable, sen aceite de palma, papel kraft compostable.",
                    ),
                    "eu": (
                        "Oliba Oliodun Xaboi Artisaua",
                        "Oliba olio birjina estra ekologikoarekin eta izpilikuarekin egindako xaboi botanikoa.",
                        "Formula biodegradagarria, palma-oliorik gabe, kraft paper konpostagarria.",
                    ),
                },
            },
        ]

        created_products = []
        for pdata in products_data:
            product, created = Product.objects.get_or_create(
                name=f"[DEMO] {pdata['name']}",
                defaults={
                    "category": pdata["category"],
                    "origin": "Fictional demo location — not a real product origin.",
                    "description": (
                        "Synthetic demo record. This is not a real product or verified claim."
                    ),
                    "sustainability_info": (
                        "Placeholder only. No sustainability claim or certification is verified."
                    ),
                    "created_by": admin_user,
                },
            )
            if created:
                record_event(
                    user=admin_user,
                    action="created",
                    entity="catalog.Product",
                    entity_id=product.pk,
                )
            for locale, (t_name, _t_desc, _t_sust) in pdata["translations"].items():
                ProductTranslation.objects.update_or_create(
                    product=product,
                    locale=locale,
                    defaults={
                        "name": f"[DEMO] {t_name}",
                        "description": "Synthetic demo record; not a real product description.",
                        "sustainability_info": (
                            "Placeholder only; no sustainability claim is verified."
                        ),
                    },
                )
            created_products.append(product)

        today = timezone.localdate()
        tasks_data = [
            (
                "Verify GOTS certificate renewal for Q4 batch",
                "Confirm updated supplier certification document before restocking.",
                created_products[0],
                OperationalTask.Status.IN_PROGRESS,
                OperationalTask.Priority.HIGH,
                today + timedelta(days=3),
            ),
            (
                "Review recycled glass packaging durability",
                "Check transit breakage notes from Valencia workshop.",
                created_products[1],
                OperationalTask.Status.TODO,
                OperationalTask.Priority.NORMAL,
                today + timedelta(days=7),
            ),
            (
                "Complete multilingual catalogue labels for Girona soap line",
                "Validate Catalan, Spanish, and Portuguese ingredient notes.",
                created_products[2],
                OperationalTask.Status.DONE,
                OperationalTask.Priority.LOW,
                today - timedelta(days=2),
            ),
        ]

        for title, desc, prod, status, priority, due in tasks_data:
            task, created = OperationalTask.objects.get_or_create(
                title=title,
                defaults={
                    "description": desc,
                    "product": prod,
                    "status": status,
                    "priority": priority,
                    "assigned_to": admin_user,
                    "created_by": admin_user,
                    "updated_by": admin_user,
                    "due_date": due,
                },
            )
            if created:
                record_event(
                    user=admin_user,
                    action="created",
                    entity="operations.OperationalTask",
                    entity_id=task.pk,
                )

        self.stdout.write(self.style.SUCCESS("Demo data and default groups seeded successfully."))
