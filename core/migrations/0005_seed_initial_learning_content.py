from django.db import migrations


def seed_learning_content(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    LessonCategory = apps.get_model("core", "LessonCategory")
    Lesson = apps.get_model("core", "Lesson")
    LessonPhrase = apps.get_model("core", "LessonPhrase")
    PhraseCategory = apps.get_model("core", "PhraseCategory")
    Phrase = apps.get_model("core", "Phrase")

    author = User.objects.filter(role="ADMIN").order_by("id").first()
    if author is None:
        author, _ = User.objects.get_or_create(
            username="bisdak.admin",
            defaults={
                "email": "admin@bisdakbasics.local",
                "first_name": "Bito",
                "last_name": "Guide",
                "role": "ADMIN",
                "is_staff": True,
                "is_active": True,
                "password": "!",
            },
        )

    categories_data = [
        {
            "name": "Greetings",
            "slug": "greetings",
            "description": "Start everyday conversations with warm Cebuano greetings for morning, afternoon, and evening.",
            "lesson": {
                "title": "Greetings",
                "slug": "greetings",
                "situation": "Say hello",
                "summary": "Start with a warm Cebuano greeting for morning, afternoon, and everyday hellos.",
                "learning_objectives": "Greet people politely at any time of day and ask how they are doing.",
                "difficulty": "BEGINNER",
                "estimated_minutes": 5,
                "position": 0,
                "cebuano_text": "Maayong buntag! Kumusta ka?\nMaayo ra ko, salamat.",
                "english_translation": "Good morning! How are you?\nI am doing well, thank you.",
                "notes": "Add 'po' is Tagalog; in Cebuano, a warm tone and 'salamat' show respect.",
                "checkpoint_question": 'How do you greet someone "Good morning!" in Cebuano?',
                "checkpoint_option_a": "Maayong buntag!",
                "checkpoint_option_b": "Tagpila ni?",
                "checkpoint_correct_answer": "A",
                "phrases": [
                    ("Maayong buntag!", "Good morning!", "Use before noon with a warm smile."),
                    ("Maayong hapon!", "Good afternoon!", "Use from early afternoon until sunset."),
                    ("Maayong gabii!", "Good evening!", "Use when greeting someone at night."),
                    ("Kumusta ka?", "How are you?", "A friendly way to start a conversation."),
                    ("Maayo ra ko, salamat.", "I'm doing well, thank you.", "Natural reply when someone asks Kumusta ka?"),
                ],
            },
        },
        {
            "name": "Ordering Food",
            "slug": "ordering-food",
            "description": "Order meals, ask for water, and thank the server at a local carenderia or restaurant.",
            "lesson": {
                "title": "Ordering Food",
                "slug": "ordering-food",
                "situation": "At the table",
                "summary": "Order meals, ask for water, and thank the server at a local eatery.",
                "learning_objectives": "Order food and drinks politely and ask for the bill in Cebuano.",
                "difficulty": "BEGINNER",
                "estimated_minutes": 5,
                "position": 1,
                "cebuano_text": "Tubig, palihog. Unsay lami diri?\nKini lang akoa. Palihog ko sa bayranan.",
                "english_translation": "Water, please. What is delicious here?\nJust this one for me. May I have the bill, please.",
                "notes": "'Palihog' means 'please' and can be placed at the start or end of a request.",
                "checkpoint_question": 'Which phrase means "Water, please." at a restaurant?',
                "checkpoint_option_a": "Tubig, palihog.",
                "checkpoint_option_b": "Asa ang kasilyas?",
                "checkpoint_correct_answer": "A",
                "phrases": [
                    ("Tubig, palihog.", "Water, please.", "Add palihog to make any request polite."),
                    ("Unsay lami diri?", "What is delicious here?", "Great for asking for a recommendation."),
                    ("Kini lang akoa.", "Just this one for me.", "Use while pointing at a dish at an eatery."),
                    ("Palihog ko sa bayranan.", "May I have the bill, please.", "Use when you are ready to pay."),
                    ("Lami kaayo, salamat!", "Very delicious, thank you!", "A warm compliment after eating."),
                ],
            },
        },
        {
            "name": "Asking for Directions",
            "slug": "asking-for-directions",
            "description": "Learn to ask where a place is, follow simple directions, and get around town confidently.",
            "lesson": {
                "title": "Asking for Directions",
                "slug": "asking-for-directions",
                "situation": "Find your way",
                "summary": "Learn to ask where a place is, follow simple directions, and get around town.",
                "learning_objectives": "Ask for nearby places and understand left, right, and straight ahead.",
                "difficulty": "BEGINNER",
                "estimated_minutes": 5,
                "position": 2,
                "cebuano_text": "Asa ang kasilyas?\nDiretso lang, dayon liko sa tuo.",
                "english_translation": "Where is the restroom?\nGo straight, then turn right.",
                "notes": "Start location questions with 'Asa ang...' followed by the place you need.",
                "checkpoint_question": 'What do you say to ask "Where is the restroom?" in Cebuano?',
                "checkpoint_option_a": "Tagpila ni?",
                "checkpoint_option_b": "Asa ang kasilyas?",
                "checkpoint_correct_answer": "B",
                "phrases": [
                    ("Asa ang kasilyas?", "Where is the restroom?", "Start location questions with Asa ang..."),
                    ("Unsaon pag-adto sa terminal?", "How do I get to the terminal?", "Replace terminal with any destination."),
                    ("Layo ba diri?", "Is it far from here?", "Helpful before deciding to walk or ride."),
                    ("Diretso lang, dayon liko sa tuo.", "Go straight, then turn right.", "Tuo means right; wala means left."),
                    ("Lugar lang!", "Please pull over here!", "Say this when riding a jeepney to stop."),
                ],
            },
        },
        {
            "name": "Market Transactions",
            "slug": "market-transactions",
            "description": "Ask for prices, request change, and buy fresh food or goods at a local market.",
            "lesson": {
                "title": "Market transactions",
                "slug": "market-transactions",
                "situation": "At the market",
                "summary": "Ask for prices, count items, and buy fresh food or goods at a local market.",
                "learning_objectives": "Ask how much an item costs and complete a friendly market purchase.",
                "difficulty": "BEGINNER",
                "estimated_minutes": 5,
                "position": 3,
                "cebuano_text": "Tagpila ni?\nPalit ko ani, palihog. Daghang salamat!",
                "english_translation": "How much is this?\nI would like to buy this, please. Thank you very much!",
                "notes": "'Tagpila' asks for price per item or unit.",
                "checkpoint_question": 'How do you ask a vendor "How much is this?" at the market?',
                "checkpoint_option_a": "Tagpila ni?",
                "checkpoint_option_b": "Kumusta ka?",
                "checkpoint_correct_answer": "A",
                "phrases": [
                    ("Tagpila ni?", "How much is this?", "The most essential phrase for shopping."),
                    ("Naa moy sukli?", "Do you have change?", "Useful when paying with a larger bill."),
                    ("Pwede mohangyo?", "Can I ask for a discount?", "Say this politely with a friendly tone."),
                    ("Palit ko ani, palihog.", "I would like to buy this, please.", "Use when you have chosen your item."),
                    ("Daghang salamat!", "Thank you very much!", "Close every transaction warmly."),
                ],
            },
        },
    ]

    for cat_entry in categories_data:
        lesson_cat, _ = LessonCategory.objects.get_or_create(
            slug=cat_entry["slug"],
            defaults={
                "name": cat_entry["name"],
                "description": cat_entry["description"],
            },
        )
        phrase_cat, _ = PhraseCategory.objects.get_or_create(
            slug=cat_entry["slug"],
            defaults={
                "name": cat_entry["name"],
                "description": cat_entry["description"],
            },
        )

        ldata = cat_entry["lesson"]
        lesson, created = Lesson.objects.get_or_create(
            slug=ldata["slug"],
            defaults={
                "category": lesson_cat,
                "title": ldata["title"],
                "situation": ldata["situation"],
                "summary": ldata["summary"],
                "learning_objectives": ldata["learning_objectives"],
                "difficulty": ldata["difficulty"],
                "estimated_minutes": ldata["estimated_minutes"],
                "position": ldata["position"],
                "cebuano_text": ldata["cebuano_text"],
                "english_translation": ldata["english_translation"],
                "notes": ldata["notes"],
                "checkpoint_question": ldata["checkpoint_question"],
                "checkpoint_option_a": ldata["checkpoint_option_a"],
                "checkpoint_option_b": ldata["checkpoint_option_b"],
                "checkpoint_correct_answer": ldata["checkpoint_correct_answer"],
                "is_published": True,
                "created_by": author,
            },
        )

        if created or not LessonPhrase.objects.filter(lesson=lesson).exists():
            for idx, (ceb, eng, note) in enumerate(ldata["phrases"], start=1):
                LessonPhrase.objects.get_or_create(
                    lesson=lesson,
                    cebuano_text=ceb,
                    defaults={
                        "english_translation": eng,
                        "usage_note": note,
                        "position": idx,
                    },
                )

        for ceb, eng, note in ldata["phrases"]:
            Phrase.objects.get_or_create(
                category=phrase_cat,
                cebuano_text=ceb,
                defaults={
                    "english_translation": eng,
                    "situation": ldata["situation"],
                    "pronunciation_note": note,
                    "is_published": True,
                    "created_by": author,
                },
            )


def unseed_learning_content(apps, schema_editor):
    # No-op on reverse to avoid deleting user progress attached to seeded lessons.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0004_alter_user_role"),
        ("core", "0004_lesson_core_lesson_pub_cat_pos_idx_and_more"),
    ]

    operations = [
        migrations.RunPython(seed_learning_content, unseed_learning_content),
    ]
