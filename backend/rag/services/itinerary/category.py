"""Map RAG place records to app itinerary category slugs."""

from __future__ import annotations

from typing import Any

from core.text_normalization import normalize_text
from services.itinerary.catalog import get_raw_place_id, get_tags_text


def app_category_from_rag(place: dict[str, Any]) -> str:
    """
    Map RAG taxonomy to app category for preview display only.

    Important:
    - Do not use full search_text too aggressively, because it contains broad words
      such as "văn hóa", "checkin", "Hồ Tây" that can pollute category mapping.
    - Prefer rawPlaceId/name/category_main/category_sub/tags.
    """

    raw_place_id = normalize_text(get_raw_place_id(place))
    name = normalize_text(place.get("name"))
    main = normalize_text(place.get("category_main_norm") or place.get("category_main"))
    sub = normalize_text(place.get("category_sub_norm") or place.get("category_sub"))
    tags = normalize_text(get_tags_text(place))

    id_name_text = f"{raw_place_id} {name}"
    taxonomy_text = f"{main} {sub} {tags}"

    slug_id_name = (
        id_name_text.replace("-", "_")
        .replace("/", "_")
        .replace(" ", "_")
    )

    slug_taxonomy = (
        taxonomy_text.replace("-", "_")
        .replace("/", "_")
        .replace(" ", "_")
    )

    slug_text = f"{slug_id_name} {slug_taxonomy}"

    def norm_key(value: str) -> str:
        return normalize_text(value).replace("-", "_").replace(" ", "_")

    def has_in_id_name(*keywords: str) -> bool:
        for keyword in keywords:
            key = norm_key(keyword)
            if key in slug_id_name:
                return True
        return False

    def has_in_taxonomy(*keywords: str) -> bool:
        for keyword in keywords:
            key = norm_key(keyword)
            if key in slug_taxonomy:
                return True
        return False

    def has_any(*keywords: str) -> bool:
        for keyword in keywords:
            key = norm_key(keyword)
            if key in slug_text:
                return True
        return False

    # 1. Exact / strong place-name rules.
    if has_in_id_name(
        "ho hoan kiem",
        "ho-hoan-kiem",
        "ho_hoan_kiem",
        "ho tay",
        "ho-tay",
        "ho_tay",
        "cau the huc",
        "cau-the-huc",
        "cau_the_huc",
        "pho di bo ho guom",
        "pho-di-bo-ho-guom",
        "pho_di_bo_ho_guom"
    ):
        return "checkin"

    if has_in_id_name(
        "pho co ha noi",
        "pho-co-ha-noi",
        "pho_co_ha_noi"
    ):
        return "city"

    if has_in_id_name(
        "van mieu",
        "van-mieu",
        "van_mieu",
        "quoc tu giam",
        "quoc-tu-giam",
        "quoc_tu_giam",
        "hoang thanh",
        "hoang-thanh",
        "hoang_thanh",
        "hoa lo",
        "hoa-lo",
        "hoa_lo",
        "nha tu",
        "nha-tu",
        "nha_tu",
        "lang co",
        "lang-co",
        "lang_co",
        "duong lam",
        "duong-lam",
        "duong_lam",
        "bao tang",
        "bao-tang",
        "bao_tang"
    ):
        return "heritage"

    if has_in_id_name(
        "chua",
        "den",
        "phu",
        "nha tho",
        "nha-tho",
        "nha_tho",
        "tran quoc",
        "tran-quoc",
        "tran_quoc",
        "quan thanh",
        "quan-thanh",
        "quan_thanh",
        "phu tay ho",
        "phu-tay-ho",
        "phu_tay_ho",
        "kim lien",
        "kim-lien",
        "kim_lien",
        "ngoc son",
        "ngoc-son",
        "ngoc_son"
    ):
        return "religious"

    if has_in_id_name(
        "bat trang",
        "bat-trang",
        "bat_trang",
        "lang gom",
        "lang-gom",
        "lang_gom",
        "lang lua",
        "lang-lua",
        "lang_lua",
        "van phuc",
        "van-phuc",
        "van_phuc",
        "lang huong",
        "lang-huong",
        "lang_huong",
        "quang phu cau",
        "quang-phu-cau",
        "quang_phu_cau",
        "mua roi",
        "mua-roi",
        "mua_roi",
        "nha hat",
        "nha-hat",
        "nha_hat",
        "lang van hoa",
        "lang-van-hoa",
        "lang_van_hoa"
    ):
        return "culture"

    if has_in_id_name(
        "vuon quoc gia ba vi",
        "vuon-quoc-gia-ba-vi",
        "vuon_quoc_gia_ba_vi",
        "ba vi",
        "ba-vi",
        "ba_vi"
    ):
        return "mountain"

    # 2. Food.
    if has_any(
        "am thuc",
        "am-thuc",
        "am_thuc",
        "food",
        "dac san",
        "dac-san",
        "dac_san",
        "an uong",
        "an-uong",
        "an_uong",
        "pho bia",
        "pho-bia",
        "pho_bia",
        "pho ca phe",
        "pho-ca-phe",
        "pho_ca_phe",
        "cho dem",
        "cho-dem",
        "cho_dem",
        "cho dong xuan",
        "cho-dong-xuan",
        "cho_dong_xuan",
        "lang ran",
        "lang-ran",
        "lang_ran"
    ):
        return "food"

    # 3. Religious from taxonomy.
    if has_in_taxonomy(
        "tam linh",
        "tam-linh",
        "tam_linh",
        "ton giao",
        "ton-giao",
        "ton_giao",
        "chua",
        "den",
        "phu",
        "thien vien",
        "thien-vien",
        "thien_vien",
        "nha tho",
        "nha-tho",
        "nha_tho",
        "pagoda",
        "temple"
    ):
        return "religious"

    # 4. Heritage/history/museum.
    if has_in_taxonomy(
        "di tich",
        "di-tich",
        "di_tich",
        "lich su",
        "lich-su",
        "lich_su",
        "bao tang",
        "bao-tang",
        "bao_tang",
        "heritage",
        "museum",
        "di san",
        "di-san",
        "di_san"
    ):
        return "heritage"

    # 5. Culture/community/craft villages.
    if has_in_taxonomy(
        "van hoa cong dong",
        "van-hoa-cong-dong",
        "van_hoa_cong_dong",
        "lang nghe",
        "lang-nghe",
        "lang_nghe",
        "le hoi",
        "le-hoi",
        "le_hoi",
        "dan toc",
        "dan-toc",
        "dan_toc",
        "mua roi",
        "mua-roi",
        "mua_roi"
    ):
        return "culture"

    # 6. Real beach / sea / island only.
    is_urban_lake = has_in_id_name(
        "ho hoan kiem",
        "ho-hoan-kiem",
        "ho_hoan_kiem",
        "ho tay",
        "ho-tay",
        "ho_tay"
    )

    if not is_urban_lake and has_in_taxonomy(
        "bai bien",
        "bai-bien",
        "bai_bien",
        "bai tam",
        "bai-tam",
        "bai_tam",
        "bien",
        "dao",
        "vinh",
        "hon",
        "mui",
        "cu lao",
        "cu-lao",
        "cu_lao",
        "cang bien",
        "cang-bien",
        "cang_bien"
    ):
        return "beach"

    # 7. Mountain/nature adventure.
    if has_in_taxonomy(
        "nui",
        "thac",
        "hang",
        "cao nguyen",
        "cao-nguyen",
        "cao_nguyen",
        "doi cat",
        "doi-cat",
        "doi_cat",
        "suoi",
        "vuon quoc gia",
        "vuon-quoc-gia",
        "vuon_quoc_gia"
    ):
        return "mountain"

    # 8. City/urban.
    if has_any(
        "thanh pho",
        "thanh-pho",
        "thanh_pho",
        "do thi",
        "do-thi",
        "do_thi",
        "pho co",
        "pho-co",
        "pho_co",
        "old quarter",
        "old-quarter",
        "old_quarter",
        "street",
        "khu pho",
        "khu-pho",
        "khu_pho"
    ):
        return "city"

    return "nature"
