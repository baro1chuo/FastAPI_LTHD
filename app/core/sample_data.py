"""Dữ liệu MẪU để chạy thử / demo: khu vực, động vật (vi + en), tài khoản, đánh giá.

Chạy:  python -m app.core.sample_data
CHỈ THÊM bản ghi còn thiếu, không xóa / không ghi đè dữ liệu đã có trong CSDL:
- khu vực đã có tên tiếng Việt trùng -> bỏ qua
- động vật đã có tên khoa học hoặc tên hiển thị trùng -> bỏ qua
- tài khoản đã có email trùng -> bỏ qua
- user đã đánh giá động vật đó -> bỏ qua
Mọi tài khoản mẫu dùng mật khẩu SAMPLE_PASSWORD – không dùng dữ liệu này khi triển khai thật.
"""
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, init_db
from app.core.security import hash_password
from app.models.animal import Animal, AnimalTranslation
from app.models.category import Category
from app.models.role import Role
from app.models.user import User
from app.models.review import Review
from app.models.zone import Zone, ZoneTranslation

SAMPLE_PASSWORD = "12345678"

# key: (màu, giờ mở cửa, diện tích m2, (tên vi, mô tả vi), (tên en, mô tả en))
ZONES = {
    "carnivore": ("#D84315", "07h30-17h00", "12000",
                  ("Khu thú ăn thịt", "Nơi sinh sống của hổ, sư tử, gấu và các loài săn mồi lớn."),
                  ("Carnivore Zone", "Home to tigers, lions, bears and other large predators.")),
    "primate": ("#6D4C41", "07h00-17h00", "8000",
                ("Khu linh trưởng", "Các loài khỉ, vượn, voọc quý hiếm của Việt Nam và thế giới."),
                ("Primate Zone", "Rare monkeys, gibbons and langurs from Vietnam and around the world.")),
    "savanna": ("#F9A825", "07h00-17h30", "25000",
                ("Khu thảo nguyên", "Mô phỏng thảo nguyên châu Phi với voi, hươu cao cổ, ngựa vằn."),
                ("Savanna Zone", "An African savanna setting with elephants, giraffes and zebras.")),
    "bird": ("#2E7D32", "06h30-17h00", "6000",
             ("Khu chim", "Vườn chim với công, hồng hạc, đà điểu và nhiều loài chim nhiệt đới."),
             ("Bird Zone", "An aviary with peafowl, flamingos, ostriches and tropical birds.")),
    "reptile": ("#00838F", "08h00-16h30", "3000",
                ("Khu bò sát và thủy sinh", "Cá sấu, trăn, rắn, lưỡng cư và cá nước ngọt quý hiếm."),
                ("Reptile & Aquatic Zone", "Crocodiles, pythons, snakes, amphibians and rare freshwater fish.")),
}

# (tên khoa học, khu, nhóm, mức bảo tồn, đang hiển thị, độ phổ biến, bản dịch vi, bản dịch en)
# Kỳ giông Mexico để available=False (đang ẩn) làm ví dụ xóa mềm cho UC11
# bản dịch: (tên, ngoại hình, phân bố, thức ăn, tuổi thọ, mối đe dọa)
ANIMALS = (
    ("Panthera tigris", "carnivore", "mammal", "EN", True, 980,
     ("Hổ", "Mèo lớn nhất thế giới, lông vàng cam có sọc đen, mỗi cá thể có hoa văn sọc riêng.",
      "Nam Á, Đông Nam Á, Trung Quốc và vùng Viễn Đông nước Nga.", "Thịt: nai, lợn rừng, trâu rừng.",
      "10–15 năm trong tự nhiên, tới 20 năm trong nuôi nhốt.", "Săn trộm lấy da, xương; mất rừng."),
     ("Tiger", "The largest cat species, orange coat with black stripes unique to each individual.",
      "South Asia, Southeast Asia, China and the Russian Far East.", "Meat: deer, wild boar, wild buffalo.",
      "10–15 years in the wild, up to 20 in captivity.", "Poaching for skin and bones; habitat loss.")),
    ("Panthera leo", "carnivore", "mammal", "VU", True, 920,
     ("Sư tử", "Lông vàng nâu; con đực có bờm dày quanh cổ. Sống theo bầy đàn.",
      "Châu Phi cận Sahara và một quần thể nhỏ ở Ấn Độ.", "Thịt: linh dương, ngựa vằn, trâu rừng.",
      "10–14 năm trong tự nhiên.", "Mất môi trường sống, xung đột với con người."),
     ("Lion", "Tawny coat; males have a thick mane. Lives in social groups called prides.",
      "Sub-Saharan Africa and a small population in India.", "Meat: antelopes, zebras, buffalo.",
      "10–14 years in the wild.", "Habitat loss and conflict with humans.")),
    ("Ursus thibetanus", "carnivore", "mammal", "VU", True, 540,
     ("Gấu ngựa", "Lông đen, có vệt lông trắng hình chữ V trên ngực.",
      "Rừng núi châu Á, gồm cả miền Bắc Việt Nam.", "Ăn tạp: quả, mật ong, côn trùng, động vật nhỏ.",
      "Khoảng 25 năm.", "Nuôi lấy mật, săn bắt, mất rừng."),
     ("Asian black bear", "Black fur with a white V-shaped patch on the chest.",
      "Forested mountains of Asia, including northern Vietnam.", "Omnivore: fruit, honey, insects, small animals.",
      "About 25 years.", "Bile farming, hunting and deforestation.")),
    ("Ailurus fulgens", "carnivore", "mammal", "EN", True, 610,
     ("Gấu trúc đỏ", "Cỡ con mèo nhà, lông nâu đỏ, đuôi dài có khoanh.",
      "Rừng ôn đới vùng Himalaya và Tây Nam Trung Quốc.", "Chủ yếu lá tre, thêm quả và trứng chim.",
      "8–10 năm.", "Mất và chia cắt rừng, săn bắt."),
     ("Red panda", "House-cat sized with reddish-brown fur and a long ringed tail.",
      "Temperate forests of the Himalayas and southwestern China.", "Mainly bamboo leaves, plus fruit and eggs.",
      "8–10 years.", "Habitat loss and fragmentation, hunting.")),
    ("Pygathrix nemaeus", "primate", "mammal", "CR", True, 760,
     ("Voọc chà vá chân nâu", "Mặt vàng cam, chân nâu đỏ, được gọi là 'nữ hoàng linh trưởng'.",
      "Trung Bộ Việt Nam, Lào và Campuchia.", "Lá non, quả, hoa.",
      "Khoảng 25 năm.", "Săn bắt và mất rừng."),
     ("Red-shanked douc", "Golden-orange face and maroon legs, called the 'queen of primates'.",
      "Central Vietnam, Laos and Cambodia.", "Young leaves, fruit, flowers.",
      "About 25 years.", "Hunting and deforestation.")),
    ("Nomascus leucogenys", "primate", "mammal", "CR", True, 430,
     ("Vượn đen má trắng", "Con đực lông đen má trắng, con cái lông vàng nhạt. Hót vang vào buổi sáng.",
      "Bắc Lào, Tây Bắc Việt Nam và Vân Nam (Trung Quốc).", "Quả chín, lá non, côn trùng.",
      "Khoảng 30 năm.", "Săn bắt làm thú cưng, mất rừng."),
     ("Northern white-cheeked gibbon", "Males are black with white cheeks, females pale yellow. Sings loudly at dawn.",
      "Northern Laos, northwestern Vietnam and Yunnan (China).", "Ripe fruit, young leaves, insects.",
      "About 30 years.", "Pet trade hunting and deforestation.")),
    ("Elephas maximus", "savanna", "mammal", "EN", True, 890,
     ("Voi châu Á", "Nhỏ hơn voi châu Phi, tai nhỏ, chỉ con đực có ngà dài.",
      "Ấn Độ, Đông Nam Á, gồm cả Tây Nguyên Việt Nam.", "Cỏ, lá, vỏ cây, quả.",
      "60–70 năm.", "Mất môi trường sống, săn lấy ngà."),
     ("Asian elephant", "Smaller than the African elephant, small ears; only males grow long tusks.",
      "India and Southeast Asia, including Vietnam's Central Highlands.", "Grass, leaves, bark, fruit.",
      "60–70 years.", "Habitat loss and poaching for ivory.")),
    ("Giraffa camelopardalis", "savanna", "mammal", "VU", True, 820,
     ("Hươu cao cổ", "Động vật cao nhất trên cạn, có thể cao gần 6 m, lông có đốm nâu.",
      "Thảo nguyên châu Phi.", "Lá cây keo và các cây bụi cao.",
      "20–25 năm.", "Mất môi trường sống, săn trộm."),
     ("Giraffe", "The tallest land animal, nearly 6 m tall, with a brown patched coat.",
      "African savannas.", "Acacia leaves and tall shrubs.",
      "20–25 years.", "Habitat loss and poaching.")),
    ("Equus quagga", "savanna", "mammal", "NT", True, 650,
     ("Ngựa vằn", "Sọc đen trắng, mỗi con có hoa văn sọc riêng như vân tay.",
      "Thảo nguyên Đông và Nam châu Phi.", "Cỏ.",
      "Khoảng 25 năm.", "Săn bắt và mất đồng cỏ."),
     ("Plains zebra", "Black and white stripes, each pattern unique like a fingerprint.",
      "Grasslands of eastern and southern Africa.", "Grass.",
      "About 25 years.", "Hunting and loss of grassland.")),
    ("Hippopotamus amphibius", "savanna", "mammal", "VU", True, 580,
     ("Hà mã", "Thân to, da dày, dành phần lớn ban ngày ngâm mình dưới nước.",
      "Sông hồ châu Phi cận Sahara.", "Cỏ, ăn vào ban đêm.",
      "40–50 năm.", "Săn lấy thịt và răng nanh, mất nguồn nước."),
     ("Hippopotamus", "Huge body and thick skin; spends most of the day in water.",
      "Rivers and lakes of sub-Saharan Africa.", "Grass, grazed at night.",
      "40–50 years.", "Hunting for meat and ivory teeth, loss of water sources.")),
    ("Pavo muticus", "bird", "bird", "EN", True, 700,
     ("Công lục", "Lông xanh lục ánh kim, con trống có đuôi dài xòe hình quạt.",
      "Đông Nam Á, gồm cả Việt Nam.", "Hạt, côn trùng, bò sát nhỏ.",
      "Khoảng 20 năm.", "Săn bắt, bẫy, mất rừng."),
     ("Green peafowl", "Iridescent green plumage; males have a long fan-shaped train.",
      "Southeast Asia, including Vietnam.", "Seeds, insects, small reptiles.",
      "About 20 years.", "Hunting, trapping and deforestation.")),
    ("Phoenicopterus roseus", "bird", "bird", "LC", True, 520,
     ("Hồng hạc lớn", "Lông hồng nhạt, chân dài, thường đứng một chân.",
      "Châu Phi, Nam Âu, Trung Đông và Nam Á.", "Tôm nhỏ, tảo, lọc qua mỏ.",
      "30–40 năm.", "Mất vùng đất ngập nước."),
     ("Greater flamingo", "Pale pink feathers, long legs, often stands on one leg.",
      "Africa, southern Europe, the Middle East and South Asia.", "Small shrimp and algae, filtered through the beak.",
      "30–40 years.", "Loss of wetlands.")),
    ("Struthio camelus", "bird", "bird", "LC", True, 480,
     ("Đà điểu châu Phi", "Chim lớn nhất thế giới, không bay được nhưng chạy tới khoảng 70 km/h.",
      "Thảo nguyên và vùng khô hạn châu Phi.", "Cây cỏ, hạt, côn trùng.",
      "30–40 năm.", "Săn bắt, mất môi trường sống."),
     ("Common ostrich", "The largest bird; cannot fly but runs at about 70 km/h.",
      "Savannas and arid regions of Africa.", "Plants, seeds, insects.",
      "30–40 years.", "Hunting and habitat loss.")),
    ("Crocodylus siamensis", "reptile", "reptile", "CR", True, 600,
     ("Cá sấu Xiêm", "Dài 3–4 m, mõm rộng, da màu xanh ô liu.",
      "Đông Nam Á; Việt Nam còn quần thể ở Vườn quốc gia Cát Tiên.", "Cá, ếch, rắn, thú nhỏ.",
      "Khoảng 50 năm.", "Mất vùng đất ngập nước, lai tạp với loài khác trong trại nuôi."),
     ("Siamese crocodile", "3–4 m long with a broad snout and olive-green skin.",
      "Southeast Asia; Vietnam has a population in Cat Tien National Park.", "Fish, frogs, snakes, small mammals.",
      "About 50 years.", "Wetland loss and hybridisation in farms.")),
    ("Malayopython reticulatus", "reptile", "reptile", "LC", True, 450,
     ("Trăn gấm", "Một trong những loài rắn dài nhất thế giới, hoa văn hình mắt lưới.",
      "Đông Nam Á và Nam Á.", "Thú và chim, giết mồi bằng cách siết.",
      "20–25 năm.", "Săn lấy da."),
     ("Reticulated python", "One of the longest snakes in the world, with a net-like pattern.",
      "Southeast and South Asia.", "Mammals and birds, killed by constriction.",
      "20–25 years.", "Hunting for skin.")),
    ("Ophiophagus hannah", "reptile", "reptile", "VU", True, 560,
     ("Rắn hổ mang chúa", "Loài rắn độc dài nhất thế giới, có thể dựng cao phần đầu khi bị đe dọa.",
      "Rừng Nam Á và Đông Nam Á.", "Chủ yếu là các loài rắn khác.",
      "Khoảng 20 năm.", "Mất rừng, buôn bán làm thuốc."),
     ("King cobra", "The world's longest venomous snake, raises its head high when threatened.",
      "Forests of South and Southeast Asia.", "Mainly other snakes.",
      "About 20 years.", "Deforestation and trade for medicine.")),
    ("Ambystoma mexicanum", "reptile", "amphibian", "CR", False, 390,
     ("Kỳ giông Mexico", "Giữ dạng ấu trùng suốt đời, có mang ngoài dạng lông vũ, tái tạo được chi.",
      "Chỉ còn ở hệ kênh hồ Xochimilco, Mexico.", "Giun, ấu trùng côn trùng, cá nhỏ.",
      "10–15 năm.", "Ô nhiễm nước, đô thị hóa, cá ngoại lai."),
     ("Axolotl", "Stays in larval form for life, with feathery external gills; can regrow limbs.",
      "Only in the Xochimilco canal system, Mexico.", "Worms, insect larvae, small fish.",
      "10–15 years.", "Water pollution, urbanisation, invasive fish.")),
    ("Scleropages formosus", "reptile", "fish", "EN", True, 410,
     ("Cá rồng châu Á", "Thân dài, vảy lớn óng ánh, có hai râu ở cằm.",
      "Sông hồ Đông Nam Á.", "Cá nhỏ, côn trùng, ếch.",
      "Trên 20 năm.", "Đánh bắt làm cá cảnh, mất môi trường sống."),
     ("Asian arowana", "Long body, large shiny scales, two barbels on the chin.",
      "Rivers and lakes of Southeast Asia.", "Small fish, insects, frogs.",
      "Over 20 years.", "Collection for the aquarium trade, habitat loss.")),
)

# (họ tên, email, vai trò) – tài khoản mẫu, mật khẩu SAMPLE_PASSWORD
USERS = (
    ("Quản trị viên", "admin@zooguide.vn", "admin"),
    ("Nguyễn Văn An", "an@zooguide.vn", "user"),
    ("Trần Thị Bình", "binh@zooguide.vn", "user"),
    ("John Smith", "john@zooguide.vn", "user"),
    ("Lê Minh Châu", "chau@zooguide.vn", "user"),
)

# (email người viết, tên khoa học, số sao, bình luận, trạng thái, ngôn ngữ)
REVIEWS = (
    ("an@zooguide.vn", "Panthera tigris", 5, "Hổ rất đẹp, chuồng rộng và sạch sẽ.", "approved", "vi"),
    ("binh@zooguide.vn", "Panthera tigris", 4, "Đến vào buổi sáng thì hổ hoạt động nhiều hơn.", "approved", "vi"),
    ("john@zooguide.vn", "Panthera tigris", 5, "Amazing tigers, very well cared for.", "approved", "en"),
    ("an@zooguide.vn", "Elephas maximus", 4, "Voi hiền, có khu cho trẻ em xem gần.", "approved", "vi"),
    ("john@zooguide.vn", "Giraffa camelopardalis", 5, "Feeding the giraffes was the highlight of our trip!", "approved", "en"),
    ("chau@zooguide.vn", "Pygathrix nemaeus", 5, "Lần đầu thấy voọc chà vá chân nâu, màu lông rất đẹp.", "approved", "vi"),
    ("binh@zooguide.vn", "Pavo muticus", 4, "Công xòe đuôi đúng lúc mình đến, may mắn quá.", "approved", "vi"),
    ("chau@zooguide.vn", "Panthera leo", 3, "Sư tử ngủ suốt, hơi tiếc.", "approved", "vi"),
    ("an@zooguide.vn", "Crocodylus siamensis", 4, "Biển giới thiệu dễ hiểu.", "pending", "vi"),
    ("john@zooguide.vn", "Ailurus fulgens", 5, "So cute, hard to spot though.", "pending", "en"),
    ("binh@zooguide.vn", "Hippopotamus amphibius", 2, "Nước trong hồ hơi đục.", "pending", "vi"),
    ("chau@zooguide.vn", "Ophiophagus hannah", 1, "Nội dung không liên quan, đã bị ẩn.", "hidden", "vi"),
)


def _zone_id_by_name(db: Session, name: str, lang: str) -> int | None:
    """id khu vực có tên này trong ngôn ngữ lang (UNIQUE(lang, name)); không có thì None."""
    return db.scalar(select(ZoneTranslation.zone_id).where(ZoneTranslation.lang == lang,
                                                          ZoneTranslation.name == name))


def _animal_name_taken(db: Session, name: str, lang: str) -> bool:
    """Tên hiển thị đã có ở động vật nào trong ngôn ngữ lang chưa (UNIQUE(lang, name))."""
    return db.scalar(select(AnimalTranslation.animal_id).where(AnimalTranslation.lang == lang,
                                                              AnimalTranslation.name == name)) is not None


def load_sample_data(db: Session) -> dict[str, int]:
    """Thêm dữ liệu mẫu còn thiếu trong MỘT giao dịch, không xóa/sửa bản ghi đã có.

    Trả số bản ghi mới thêm theo từng loại: {"zones", "animals", "users", "reviews"}.
    """
    added = {"zones": 0, "animals": 0, "users": 0, "reviews": 0}

    # Khu vực: dùng lại khu đã có cùng tên tiếng Việt hoặc tiếng Anh
    zone_ids = {}
    for key, (color, hours, area, vi, en) in ZONES.items():
        zone_id = _zone_id_by_name(db, vi[0], "vi") or _zone_id_by_name(db, en[0], "en")
        if zone_id is None:
            zone = Zone(color=color, open_hours=hours, area_m2=Decimal(area))
            db.add(zone)
            db.flush()
            zone_id = zone.id
            db.add_all([ZoneTranslation(zone_id=zone_id, lang="vi", name=vi[0], description=vi[1]),
                        ZoneTranslation(zone_id=zone_id, lang="en", name=en[0], description=en[1])])
            added["zones"] += 1
        zone_ids[key] = zone_id

    # Động vật: bỏ qua nếu trùng tên khoa học hoặc trùng tên hiển thị
    category_ids = dict(db.execute(select(Category.code, Category.id)).all())
    fields = ("name", "appearance", "distribution", "diet", "lifespan", "threat")
    for sci, zone, category, status, available, popularity, vi, en in ANIMALS:
        if (db.scalar(select(Animal.id).where(Animal.scientific_name == sci)) is not None
                or _animal_name_taken(db, vi[0], "vi") or _animal_name_taken(db, en[0], "en")):
            continue
        animal = Animal(scientific_name=sci, zone_id=zone_ids[zone], category_id=category_ids[category],
                        conservation_status_code=status, available=available, popularity=popularity)
        db.add(animal)
        db.flush()
        for lang, values in (("vi", vi), ("en", en)):
            db.add(AnimalTranslation(animal_id=animal.id, lang=lang, **dict(zip(fields, values))))
        added["animals"] += 1
    db.flush()

    # Tài khoản: bỏ qua nếu email đã có (không đổi mật khẩu tài khoản cũ)
    role_ids = dict(db.execute(select(Role.code, Role.id)).all())
    password_hash = hash_password(SAMPLE_PASSWORD)  # băm 1 lần dùng chung cho mọi tài khoản mẫu
    for full_name, email, role in USERS:
        if db.scalar(select(User.id).where(User.email == email)) is None:
            db.add(User(full_name=full_name, email=email, role_id=role_ids[role], password_hash=password_hash))
            added["users"] += 1
    db.flush()

    # Đánh giá: mỗi user 1 đánh giá / động vật -> bỏ qua nếu đã có
    user_ids = dict(db.execute(select(User.email, User.id)).all())
    animal_ids = dict(db.execute(select(Animal.scientific_name, Animal.id)).all())
    for email, sci, rating, comment, status, lang in REVIEWS:
        user_id, animal_id = user_ids.get(email), animal_ids.get(sci)
        if user_id is None or animal_id is None:
            continue
        if db.scalar(select(Review.id).where(Review.user_id == user_id, Review.animal_id == animal_id)) is None:
            db.add(Review(user_id=user_id, animal_id=animal_id, rating=rating,
                          comment=comment, status=status, lang=lang))
            added["reviews"] += 1

    db.commit()
    return added


if __name__ == "__main__":
    init_db()
    with SessionLocal() as session:
        result = load_sample_data(session)
    print(f"Đã thêm {result['zones']} khu vực, {result['animals']} động vật, "
          f"{result['users']} tài khoản (mật khẩu {SAMPLE_PASSWORD}), {result['reviews']} đánh giá. "
          "Dữ liệu đã có được giữ nguyên.")
