"""Maintain English and Khmer catalogs from aligned translation rows."""
import json
from pathlib import Path

ROWS = '''
welcome_hero|WELCOME TO Empress Cambodia|ស្វាគមន៍មកកាន់ Empress Cambodia
reference_hero_heading|Simple care. Everyday comfort.|ការថែទាំសាមញ្ញ សម្រាប់រាល់ថ្ងៃ។
reference_hero_description|Thoughtful skincare, a calmer routine, and a little time for yourself.|ការថែរក្សាស្បែកដោយយកចិត្តទុកដាក់ ទម្លាប់ដ៏សាមញ្ញ និងពេលវេលាបន្តិចសម្រាប់ខ្លួនអ្នក។
contact_us|Contact us|ទាក់ទងយើង
alt_soap_hero|Blush pink soap packaging and two-tone artisan soap bars, an original illustrative collection.|ប្រអប់សាប៊ូពណ៌ផ្កាឈូក និងដុំសាប៊ូពីរពណ៌ ជាបណ្តុំរូបភាពគំរូដើម។
product_details|Ask about this product|សួរអំពីផលិតផលនេះ
show_password|Show password|បង្ហាញពាក្យសម្ងាត់
hide_password|Hide password|លាក់ពាក្យសម្ងាត់
care_intro|Care that fits your day.|ការថែទាំដែលសមនឹងជីវិតប្រចាំថ្ងៃ។
collection_simple|Explore the collection|ស្វែងយល់ពីផលិតផល
gallery_simple|A closer look|មើលរូបភាពបន្ថែម
home_title|Home|ទំព័រដើម
about_title|Our story|រឿងរ៉ាវរបស់យើង
retailers_title|Find a retailer|ស្វែងរកហាង
contact_title|Contact|ទំនាក់ទំនង
admin_title|Admin|អ្នកគ្រប់គ្រង
error_title|Something went wrong|មានបញ្ហាកើតឡើង
meta_description|Discover Empress Cambodia: a thoughtful skincare concept inspired by nature, simple routines, and everyday wellbeing.|ស្វែងយល់ពី Empress Cambodia៖ គំនិតថែរក្សាស្បែកដែលផ្តោតលើធម្មជាតិ ទម្លាប់សាមញ្ញ និងសុខុមាលភាពប្រចាំថ្ងៃ។
skip|Skip to content|រំលងទៅមាតិកា
announcement|A little nature. A little nurture.|ធម្មជាតិបន្តិច ការថែទាំបន្តិច។
announcement_end|Your daily ritual, reimagined.|ទម្លាប់ថែទាំប្រចាំថ្ងៃតាមរបៀបថ្មី។
brand_tagline|NATURE MEETS EVERYDAY CARE|ធម្មជាតិ និងការថែទាំប្រចាំថ្ងៃ
menu|Open navigation|បើកម៉ឺនុយ
navigation|Main navigation|ម៉ឺនុយចម្បង
discover|Discover our range|ស្វែងយល់ផលិតផល
hero_eyebrow|ROOTED IN NATURE. MADE FOR YOU.|ផ្អែកលើធម្មជាតិ។ សម្រាប់អ្នក។
hero_title|A softer touch.|ការថែទាំទន់ភ្លន់។
hero_emphasis|A natural glow.|សម្រស់តាមធម្មជាតិ។
hero_description|Slow down. Breathe in. Discover thoughtful skincare that turns the everyday into a little moment of paradise.|បន្ថយល្បឿន ដកដង្ហើម និងស្វែងយល់ការថែរក្សាស្បែកដែលប្រែក្លាយថ្ងៃធម្មតាទៅជាពេលវេលាដ៏រីករាយ។
explore_collection|Explore the collection|មើលបណ្តុំផលិតផល
our_story|Our story|រឿងរ៉ាវរបស់យើង
hero_note|Good things grow naturally.|អ្វីដែលល្អលូតលាស់តាមធម្មជាតិ។
hero_note_small|Thoughtful care. Beautifully simple.|ការថែទាំដោយយកចិត្តទុកដាក់ និងសាមញ្ញ។
image_caption|THE ART OF EVERYDAY CARE|សិល្បៈនៃការថែទាំប្រចាំថ្ងៃ
stamp_top|INSPIRED BY|បំផុសគំនិតដោយ
stamp_bottom|NATURE|ធម្មជាតិ
value_botanical|Botanical inspiration|បំផុសគំនិតពីរុក្ខជាតិ
value_simple|Simple rituals|ទម្លាប់សាមញ្ញ
value_mindful|Mindful by design|រចនាដោយយកចិត្តទុកដាក់
value_daily|Everyday wellbeing|សុខុមាលភាពប្រចាំថ្ងៃ
intro_eyebrow|WELCOME TO Empress Cambodia|ស្វាគមន៍មកកាន់ Empress Cambodia
intro_title|Beautiful care begins|ការថែទាំដ៏ល្អចាប់ផ្តើម
intro_emphasis|with the little things.|ពីរឿងតូចៗ។
intro_description|A quiet moment. A familiar scent. The feeling of starting fresh. We believe the most meaningful skincare routines are the ones that bring you back to yourself.|ពេលស្ងប់ស្ងាត់ ក្លិនដែលធ្លាប់ស្គាល់ និងអារម្មណ៍ស្រស់ស្រាយ។ យើងជឿថាទម្លាប់ថែស្បែកដ៏មានន័យគឺជួយឱ្យអ្នកមានអារម្មណ៍ល្អឡើងវិញ។
meet_brand|Get to know us|ស្គាល់យើងបន្ថែម
ritual_eyebrow|A LITTLE CARE GOES A LONG WAY|ការថែទាំតិចតួចមានន័យច្រើន
ritual_title|For your skin.|សម្រាប់ស្បែកអ្នក។
ritual_emphasis|For your senses.|សម្រាប់អារម្មណ៍អ្នក។
skincare|Skincare, made simple|ការថែស្បែកដ៏សាមញ្ញ
skincare_description|Explore a considered approach to cleansing, moisture, and the small routines that help you feel cared for.|ស្វែងយល់ពីការសម្អាត ការផ្តល់សំណើម និងទម្លាប់តូចៗដែលធ្វើឱ្យអ្នកមានអារម្មណ៍ថាបានថែទាំល្អ។
wellness|Wellness, in the everyday|សុខុមាលភាពក្នុងជីវិតប្រចាំថ្ងៃ
wellness_description|Make room for an unhurried morning or a restful evening. Your daily ritual can be a moment just for you.|ទុកពេលសម្រាប់ព្រឹកដ៏ស្ងប់ស្ងាត់ ឬល្ងាចដ៏សម្រាក។ ទម្លាប់ប្រចាំថ្ងៃអាចជាពេលវេលាសម្រាប់អ្នកផ្ទាល់។
our_philosophy|Our philosophy|ទស្សនវិជ្ជារបស់យើង
nature_label|NATURE IS OUR STARTING POINT|ធម្មជាតិជាចំណុចចាប់ផ្តើម
collection_eyebrow|THE EVERYDAY EDIT|ការថែទាំប្រចាំថ្ងៃ
collection_title|Meet your new|ជួបទម្លាប់ថ្មី
collection_emphasis|daily ritual.|ប្រចាំថ្ងៃរបស់អ្នក។
find_nearby|Find a retailer near you|ស្វែងរកហាងក្បែរអ្នក
serum_name|The Daily Glow|សម្រស់ប្រចាំថ្ងៃ
serum_tag|THE MORNING RITUAL|ទម្លាប់ពេលព្រឹក
serum_description|A bright beginning to your day.|ចាប់ផ្តើមថ្ងៃដ៏ស្រស់ស្រាយ។
cleanser_name|The Fresh Start|ការចាប់ផ្តើមថ្មី
cleanser_tag|THE CLEANSING RITUAL|ទម្លាប់សម្អាត
cleanser_description|A clean slate. A moment to reset.|ភាពស្អាត និងពេលចាប់ផ្តើមឡើងវិញ។
cream_name|The Soft Touch|ភាពទន់ភ្លន់
cream_tag|THE EVENING RITUAL|ទម្លាប់ពេលល្ងាច
cream_description|An invitation to slow things down.|ការអញ្ជើញឱ្យសម្រាកបន្តិច។
collection_disclaimer|An illustrative skincare collection. Photography is for visual inspiration; ask us about product availability and ingredients.|នេះជាបណ្តុំផលិតផលគំរូ។ រូបថតប្រើសម្រាប់បំផុសគំនិត សូមសួរយើងអំពីផលិតផលដែលមាន និងគ្រឿងផ្សំ។
gentle|A gentler approach|វិធីថែទាំទន់ភ្លន់
gentle_description|A simpler routine, with room to find what feels right for your skin.|ទម្លាប់សាមញ្ញ និងពេលស្វែងរកអ្វីដែលសមនឹងស្បែកអ្នក។
balance|A moment of balance|ពេលវេលានៃតុល្យភាព
balance_description|Bring a little calm to the beginning and end of every day.|នាំភាពស្ងប់ស្ងាត់មកពេលចាប់ផ្តើម និងបញ្ចប់ថ្ងៃ។
considered|Care, considered|ការថែទាំដោយគិតគូរ
considered_description|Ask questions. Know your routine. Make thoughtful choices.|សួរសំណួរ ស្គាល់ទម្លាប់អ្នក និងជ្រើសរើសដោយយកចិត្តទុកដាក់។
gallery_eyebrow|THROUGH OUR LENS|តាមរយៈកែវថតយើង
gallery_title|Everyday moments,|ពេលវេលាប្រចាំថ្ងៃ
gallery_emphasis|beautifully captured.|ថតទុកយ៉ាងស្រស់ស្អាត។
visual_journal|Visual journal|កំណត់ហេតុរូបភាព
view_image|View image|មើលរូបភាព
light_caption|A little light, a little ritual|ពន្លឺបន្តិច ទម្លាប់បន្តិច
nature_caption|Back to the source|ត្រឡប់ទៅប្រភពដើម
slow_caption|The beauty of slowing down|សម្រស់នៃការរស់យឺតៗ
close|Close|បិទ
promise_eyebrow|OUR APPROACH|វិធីសាស្ត្ររបស់យើង
promise_title|Good for your ritual.|ល្អសម្រាប់ទម្លាប់អ្នក។
promise_emphasis|Rooted in care.|ផ្អែកលើការយកចិត្តទុកដាក់។
promise_description|We are building a skincare concept around a simple idea: feeling good in your skin should feel uncomplicated.|យើងកសាងគំនិតថែរក្សាស្បែកលើគោលការណ៍ថា ការមានអារម្មណ៍ល្អជាមួយស្បែកគួរតែសាមញ្ញ។
read_story|Read our story|អានរឿងរ៉ាវយើង
why_choose|Why choose our approach|ហេតុអ្វីជ្រើសរើសវិធីសាស្ត្រយើង
why_description|Clarity over complexity. We make room for questions, thoughtful routines, and personal choices, without promising a one-size-fits-all solution.|យើងផ្តោតលើភាពច្បាស់លាស់ សំណួរ និងជម្រើសផ្ទាល់ខ្លួន ព្រោះស្បែកមនុស្សម្នាក់ៗខុសគ្នា។
commitment|Our commitment|ការប្តេជ្ញារបស់យើង
commitment_description|We aim to communicate openly about ingredients, packaging, and the choices behind every product. Ask us what matters to you.|យើងមានគោលបំណងផ្តល់ព័ត៌មានច្បាស់អំពីគ្រឿងផ្សំ ការវេចខ្ចប់ និងជម្រើសពីក្រោយផលិតផល។ សួរយើងអំពីអ្វីដែលអ្នកចង់ដឹង។
inquiry_eyebrow|LET'S GROW TOGETHER|រីកចម្រើនជាមួយគ្នា
inquiry_title|A beautiful partnership|ភាពជាដៃគូដ៏ល្អ
inquiry_emphasis|starts here.|ចាប់ផ្តើមទីនេះ។
inquiry_description|Interested in bringing our concept to your shelves? We would love to hear from you.|ចាប់អារម្មណ៍នាំគំនិតរបស់យើងទៅកាន់ហាងអ្នក? យើងរីករាយក្នុងការស្តាប់ពីអ្នក។
lets_talk|Let's talk|តោះនិយាយគ្នា
footer_description|A thoughtful approach to skincare. Inspired by nature and the beauty of everyday moments.|ការថែស្បែកដោយគិតគូរ បំផុសគំនិតពីធម្មជាតិ និងសម្រស់នៃពេលវេលាប្រចាំថ្ងៃ។
explore|Explore|ស្វែងយល់
connect|Get in touch|ទាក់ទងយើង
general_inquiry|General inquiries|សំណួរទូទៅ
partnership|Retail partnerships|ភាពជាដៃគូហាង
little_ritual|A little ritual. A better day.|ទម្លាប់តូចមួយ ថ្ងៃល្អមួយ។
footer_note|Take a breath. Make a little time for yourself today.|ដកដង្ហើម ហើយទុកពេលថែខ្លួនបន្តិចថ្ងៃនេះ។
rights|All rights reserved.|រក្សាសិទ្ធិគ្រប់យ៉ាង។
concept_note|Independent skincare website concept.|គេហទំព័រគំរូថែស្បែកឯករាជ្យ។
about_eyebrow|NATURE. SIMPLICITY. YOU.|ធម្មជាតិ។ ភាពសាមញ្ញ។ អ្នក។
about_heading|Care with|ការថែទាំមាន
about_emphasis|a little more meaning.|អត្ថន័យបន្ថែម។
about_intro|An independent concept for a more thoughtful everyday. Welcome to the world of Empress Cambodia.|គំនិតឯករាជ្យសម្រាប់ការរស់នៅដោយយកចិត្តទុកដាក់។ ស្វាគមន៍មកកាន់ Empress Cambodia។
story_heading|Less rush.|បន្ថយភាពប្រញាប់។
story_emphasis|More ritual.|បន្ថែមទម្លាប់ថែទាំ។
story_p1|Empress Cambodia began as a design concept around a question: what if skincare felt less like another task, and more like a moment to come home to yourself?|Empress Cambodia ចាប់ផ្តើមពីសំណួរមួយ៖ តើការថែស្បែកអាចក្លាយជាពេលវេលាសម្រាប់ខ្លួនឯង ជំនួសឱ្យកិច្ចការបន្ថែមបានទេ?
story_p2|Our answer is a calmer, simpler experience. We take inspiration from botanical textures, natural light, and the small pleasures of a daily routine. This website presents that vision, and invites conversations about what comes next.|ចម្លើយយើងគឺបទពិសោធន៍សាមញ្ញ និងស្ងប់ស្ងាត់។ យើងបំផុសគំនិតពីរុក្ខជាតិ ពន្លឺធម្មជាតិ និងភាពរីករាយតូចៗ។ គេហទំព័រនេះបង្ហាញចក្ខុវិស័យ និងអញ្ជើញការសន្ទនា។
philosophy_heading|Small rituals. Thoughtful principles.|ទម្លាប់តូចៗ គោលការណ៍គិតគូរ។
mission|Our mission|បេសកកម្មយើង
mission_description|Make everyday self-care feel approachable, intentional, and personal.|ធ្វើឱ្យការថែខ្លួនប្រចាំថ្ងៃមានភាពងាយស្រួល មានគោលបំណង និងផ្ទាល់ខ្លួន។
vision|Our vision|ចក្ខុវិស័យយើង
vision_description|A world where taking care of yourself leaves room to care for the world around you.|ពិភពលោកដែលការថែខ្លួនផ្សារភ្ជាប់នឹងការថែពិភពជុំវិញ។
quality|Our quality approach|វិធីគិតអំពីគុណភាព
quality_description|Clear information, honest conversations, and careful product decisions. Request specific product details before choosing.|ព័ត៌មានច្បាស់លាស់ ការសន្ទនាស្មោះត្រង់ និងជម្រើសប្រុងប្រយ័ត្ន។ សូមសួរព័ត៌មានផលិតផលមុនជ្រើសរើស។
sustainability_heading|A thoughtful relationship|ទំនាក់ទំនងប្រកបដោយការគិតគូរ
sustainability_emphasis|with nature.|ជាមួយធម្មជាតិ។
sustainability_description|Sustainability is a direction, not a decorative label. Our concept prioritizes considered packaging and transparent sourcing information. Specific environmental claims will only be published when they can be verified.|និរន្តរភាពគឺជាទិសដៅ។ គំនិតយើងផ្តោតលើការវេចខ្ចប់ និងព័ត៌មានប្រភពច្បាស់លាស់។ ការអះអាងបរិស្ថាននឹងបោះផ្សាយតែនៅពេលផ្ទៀងផ្ទាត់បាន។
ask_question|Ask us a question|សួរយើងមួយសំណួរ
retailers_eyebrow|A LITTLE CLOSER TO YOU|នៅជិតអ្នកបន្តិច
retailers_heading|Find your|ស្វែងរក
retailers_emphasis|local ritual.|ហាងក្បែរអ្នក។
retailers_intro|Explore our directory by country and city. Connect with a store to confirm availability before visiting.|ស្វែងរកតាមប្រទេស និងទីក្រុង។ សូមទាក់ទងហាងដើម្បីបញ្ជាក់ផលិតផលមុនទៅ។
country|Country|ប្រទេស
city|City|ទីក្រុង
all_countries|All countries|ប្រទេសទាំងអស់
city_placeholder|Enter a city|បញ្ចូលទីក្រុង
search|Search retailers|ស្វែងរកហាង
reset|Clear filters|សម្អាតតម្រង
retailer_results|Your nearby discoveries|ហាងដែលរកឃើញ
locations|locations|ទីតាំង
example_listing|Example listing|ហាងគំរូ
directions|Get directions|មើលទិសដៅ
no_retailers|No retailers found yet.|មិនទាន់រកឃើញហាង។
no_retailers_description|Try another city, clear your filters, or ask us about availability in your area.|សាកទីក្រុងផ្សេង សម្អាតតម្រង ឬសួរយើងអំពីផលិតផលក្នុងតំបន់អ្នក។
ask_us|Ask about availability|សួរអំពីផលិតផលដែលមាន
retailer_disclaimer|Demo directory: example stores show how the locator works. These are not verified stockists. An administrator can replace them with real listings.|បញ្ជីសាកល្បង៖ ហាងគំរូបង្ហាញរបៀបស្វែងរក ហើយមិនមែនជាហាងដែលបានផ្ទៀងផ្ទាត់ទេ។ អ្នកគ្រប់គ្រងអាចជំនួសដោយហាងពិត។
contact_eyebrow|GOOD CONVERSATIONS START HERE|ការសន្ទនាល្អចាប់ផ្តើមទីនេះ
contact_heading|Let's make|តោះធ្វើអ្វី
contact_emphasis|a connection.|ភ្ជាប់ទំនាក់ទំនង។
contact_intro|Questions about our concept, products, or retail partnerships? We would love to hear what is on your mind.|មានសំណួរអំពីគំនិត ផលិតផល ឬភាពជាដៃគូ? យើងចង់ស្តាប់ពីអ្នក។
contact_aside|A little hello goes a long way.|ការសួរសុខទុក្ខតូចមួយមានន័យច្រើន។
contact_aside_description|Send your message and our team can review it in our secure inquiry inbox.|ផ្ញើសារ ហើយក្រុមយើងអាចពិនិត្យវាក្នុងប្រអប់សារដែលមានសុវត្ថិភាព។
use_form|Use the form to reach our team.|ប្រើទម្រង់ដើម្បីទាក់ទងក្រុមយើង។
partnership_description|Tell us about your store, location, and the products you are interested in.|ប្រាប់យើងអំពីហាង ទីតាំង និងផលិតផលដែលអ្នកចាប់អារម្មណ៍។
privacy|Your details are stored securely for handling your inquiry. They are not displayed publicly.|ព័ត៌មានអ្នករក្សាទុកសម្រាប់ដោះស្រាយសំណួរ ហើយមិនបង្ហាញជាសាធារណៈទេ។
send_message|Leave us a note|ទុកសារមួយដល់យើង
required_note|Fields marked * are required.|ប្រអប់សម្គាល់ * ត្រូវបំពេញ។
name|Name|ឈ្មោះ
email|Email|អ៊ីមែល
phone|Phone|ទូរស័ព្ទ
subject|Subject|ប្រធានបទ
message|Message|សារ
consent|By sending this form, you agree that we may use these details to respond to your inquiry. To request removal, send a message with the subject “Privacy request”.|ពេលផ្ញើទម្រង់នេះ អ្នកយល់ព្រមឱ្យយើងប្រើព័ត៌មានដើម្បីឆ្លើយសំណួរ។ ដើម្បីស្នើលុបព័ត៌មាន សូមផ្ញើសារប្រធានបទ “Privacy request”។
send|Send message|ផ្ញើសារ
success|Thank you. Your message has been received. Our team will review your inquiry.|អរគុណ។ យើងទទួលបានសារហើយ ក្រុមយើងនឹងពិនិត្យសំណួរអ្នក។
error_name|Please enter a name between 2 and 100 characters.|សូមបញ្ចូលឈ្មោះពី 2 ដល់ 100 តួអក្សរ។
error_subject|Please enter a subject between 3 and 160 characters.|សូមបញ្ចូលប្រធានបទពី 3 ដល់ 160 តួអក្សរ។
error_message|Please write a message between 10 and 5,000 characters.|សូមសរសេរសារពី 10 ដល់ 5,000 តួអក្សរ។
error_email|Please enter a valid email address.|សូមបញ្ចូលអាសយដ្ឋានអ៊ីមែលត្រឹមត្រូវ។
error_phone|Please enter a valid phone number, up to 30 characters.|សូមបញ្ចូលលេខទូរស័ព្ទត្រឹមត្រូវ មិនលើស 30 តួអក្សរ។
error_form|Please review the fields below and try again.|សូមពិនិត្យប្រអប់ខាងក្រោម ហើយព្យាយាមម្តងទៀត។
error_save|We could not save your message. Please try again shortly.|យើងមិនអាចរក្សាទុកសារបានទេ សូមសាកម្តងទៀតបន្តិចទៀត។
error_csrf|Your form session expired. Reload the page and try again.|វគ្គទម្រង់ផុតកំណត់ហើយ សូមផ្ទុកទំព័រឡើងវិញ។
error_400|This request could not be processed. Reload the page and try again.|មិនអាចដំណើរការសំណើ សូមផ្ទុកទំព័រឡើងវិញ។
error_404|This page could not be found. Explore the links above to find your way.|រកមិនឃើញទំព័រនេះ សូមប្រើតំណខាងលើ។
error_413|This submission is too large. Please shorten your message.|ទិន្នន័យធំពេក សូមកាត់បន្ថយសារ។
error_429|Too many requests. Please wait a minute before trying again.|មានសំណើច្រើនពេក សូមរង់ចាំមួយនាទីមុនសាកឡើងវិញ។
error_500|An unexpected error occurred. Please try again shortly.|មានបញ្ហាមិនរំពឹងទុក សូមសាកម្តងទៀត។
error_heading|A moment to reset.|សម្រាកបន្តិច ហើយចាប់ផ្តើមឡើងវិញ។
back_home|Back to home|ត្រឡប់ទំព័រដើម
admin_intro|Sign in to manage inquiries and retailer locations.|ចូលដើម្បីគ្រប់គ្រងសារ និងទីតាំងហាង។
username|Username|ឈ្មោះអ្នកប្រើ
password|Password|ពាក្យសម្ងាត់
sign_in|Sign in|ចូល
sign_out|Sign out|ចាកចេញ
login_error|The username or password is incorrect.|ឈ្មោះអ្នកប្រើ ឬពាក្យសម្ងាត់មិនត្រឹមត្រូវ។
dashboard|Your care desk.|ផ្ទាំងគ្រប់គ្រងអ្នក។
new|New|ថ្មី
read|Read|បានអាន
archived|Archived|ទុកក្នុងបណ្ណសារ
all|All|ទាំងអស់
inbox|Inquiry inbox|ប្រអប់សំណួរ
inbox_limit|Showing the latest 200 inquiries for the selected filter. Dates are in UTC.|បង្ហាញសំណួរថ្មីបំផុត 200 តាមតម្រង។ កាលបរិច្ឆេទជា UTC។
language|Language|ភាសា
received|Received|បានទទួល
reply|Reply by email|ឆ្លើយតាមអ៊ីមែល
status|Status|ស្ថានភាព
update|Update|ធ្វើបច្ចុប្បន្នភាព
no_messages|No inquiries in this view yet.|មិនទាន់មានសំណួរក្នុងទិដ្ឋភាពនេះ។
manage_retailers|Retailer directory|បញ្ជីហាង
add_retailer|Add a retailer|បន្ថែមហាង
address|Address|អាសយដ្ឋាន
save_retailer|Save retailer|រក្សាទុកហាង
delete_retailer|Delete retailer|លុបហាង
confirm_delete|Delete this retailer from the public directory? This cannot be undone.|លុបហាងនេះពីបញ្ជីសាធារណៈ? មិនអាចត្រឡប់វិញបានទេ។
error_retailer|Please complete the required fields and provide valid contact information.|សូមបំពេញប្រអប់ចាំបាច់ និងព័ត៌មានទំនាក់ទំនងត្រឹមត្រូវ។
saved|Retailer saved successfully.|រក្សាទុកហាងបានជោគជ័យ។
alt_hero|Amber glass skincare bottle on a pedestal in natural sunlight.|ដបកញ្ចក់ពណ៌អាំប៊ែរលើជើងទម្រក្រោមពន្លឺធម្មជាតិ។
alt_forest|Sunlight filtering through a lush green forest.|ពន្លឺព្រះអាទិត្យឆ្លងកាត់ព្រៃបៃតង។
alt_serum|An amber bottle in warm botanical shadows; illustrative skincare photography.|ដបពណ៌អាំប៊ែរក្រោមស្រមោលរុក្ខជាតិ រូបថតគំរូ។
alt_cleanser|A still life of skincare products; illustrative collection photography.|រូបថតផលិតផលថែស្បែកសម្រាប់បណ្តុំគំរូ។
alt_cream|Skincare packaging and soft textures; illustrative product photography.|ការវេចខ្ចប់ និងផ្ទៃទន់ រូបថតផលិតផលគំរូ។
'''

if __name__ == '__main__':
    catalogs = {lang: {} for lang in ('en', 'km')}
    for row in ROWS.strip().splitlines():
        key, *texts = row.split('|')
        assert len(texts) == 2, key
        for lang, value in zip(catalogs, texts):
            catalogs[lang][key] = value
    for lang, values in catalogs.items():
        (Path(__file__).parent / 'translations' / f'{lang}.json').write_text(json.dumps(values, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'Created two catalogs with {len(catalogs["en"])} translated strings each.')
