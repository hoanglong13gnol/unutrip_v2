#!/usr/bin/env python3
"""Generate UNUTrip BPMN draw.io – horizontal swimlanes (reference style)."""

import os
import re
import xml.etree.ElementTree as ET

OUT = os.path.join(os.path.dirname(__file__), "UNUTrip_BPMN_QuyTrinhNghiepVu.drawio")

TASK = (
    "rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#000000;"
    "shadow=1;fontFamily=Helvetica;fontSize=11;"
)
GW = (
    "rhombus;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#000000;"
    "shadow=1;fontFamily=Helvetica;fontSize=10;"
)
START = "ellipse;fillColor=#000000;strokeColor=#000000;html=1;"
END_OUTER = (
    "ellipse;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#000000;"
    "strokeWidth=2;shadow=1;html=1;"
)
END_INNER = "ellipse;fillColor=#000000;strokeColor=#000000;html=1;"
EDGE = (
    "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;"
    "html=1;strokeColor=#000000;endArrow=classic;"
)
EDGE_DASH = EDGE + "dashed=1;"
LABEL = (
    "edgeLabel;html=1;align=center;verticalAlign=middle;resizable=0;points=[];"
    "fontSize=10;fontFamily=Helvetica;"
)
POOL = (
    "swimlane;childLayout=stackLayout;horizontal=0;startSize=30;"
    "horizontalStack=0;resizeParent=1;resizeParentMax=0;resizeLast=0;"
    "collapsible=0;marginBottom=0;whiteSpace=wrap;html=1;fillColor=#f5f5f5;"
    "strokeColor=#000000;fontStyle=0;fontFamily=Helvetica;"
)
LANE = (
    "swimlane;startSize=30;horizontal=1;fillColor=#ffffff;strokeColor=#000000;"
    "fontStyle=1;fontFamily=Helvetica;fontSize=11;whiteSpace=wrap;html=1;"
)

ORIGIN_X = 40
ORIGIN_Y = 40
LANE_H = 130
POOL_W = 1540
START_SIZE = 30

_gid = 0


def uid(prefix="x"):
    global _gid
    _gid += 1
    return f"{prefix}{_gid}"


def esc(t):
    if not t:
        return ""
    return (
        str(t)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("\n", "&#xa;")
    )


def vtx(cid, value, style, x, y, w, h, parent="1"):
    return (
        f'        <mxCell id="{cid}" value="{esc(value)}" style="{style}" '
        f'vertex="1" parent="{parent}">'
        f'<mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>\n'
    )


def edg(eid, src, tgt, label="", dashed=False, parent="1"):
    st = EDGE_DASH if dashed else EDGE
    xml = (
        f'        <mxCell id="{eid}" value="" style="{st}" edge="1" '
        f'parent="{parent}" source="{src}" target="{tgt}">'
        f'<mxGeometry relative="1" as="geometry"/></mxCell>\n'
    )
    if label:
        lid = uid("el")
        xml += (
            f'        <mxCell id="{lid}" value="{esc(label)}" style="{LABEL}" '
            f'vertex="1" connectable="0" parent="{eid}">'
            f'<mxGeometry x="-0.2" relative="1" as="geometry">'
            f'<mxPoint as="offset"/></mxGeometry></mxCell>\n'
        )
    return xml


class SwimlanePage:
    """Horizontal swimlane BPMN page."""

    def __init__(self, page_idx, title, lane_names):
        self.pi = page_idx
        self.title = title
        self.lanes = lane_names
        self.nodes = {}
        self.parts = []
        self.pool_id = uid(f"p{self.pi}pool")
        self.lane_ids = [uid(f"p{self.pi}ln") for _ in lane_names]
        self.lane_y = {i: i * LANE_H for i in range(len(lane_names))}

    def _lane_abs_y(self, lane_idx):
        return ORIGIN_Y + START_SIZE + 34 + lane_idx * LANE_H + LANE_H // 2

    def _abs_pos(self, x, lane_idx, y_offset=0):
        lane_top = ORIGIN_Y + START_SIZE + 34 + lane_idx * LANE_H
        return x, lane_top + LANE_H // 2 + y_offset

    def _parent(self, lane):
        return self.lane_ids[lane]

    def _rel_pos(self, x, lane, y_off=0):
        """x = offset from lane content left (after 30px label strip)."""
        return START_SIZE + x, LANE_H // 2 + y_off

    def task(self, key, text, x, lane, w=148, h=44, y_off=0):
        rx, ry = self._rel_pos(x, lane, y_off)
        cid = uid(f"p{self.pi}")
        self.nodes[key] = cid
        parent = self._parent(lane)
        self.parts.append(vtx(cid, text, TASK, rx - w // 2, ry - h // 2, w, h, parent))
        return cid

    def gw(self, key, text, x, lane, size=68, y_off=0):
        rx, ry = self._rel_pos(x, lane, y_off)
        cid = uid(f"p{self.pi}")
        self.nodes[key] = cid
        parent = self._parent(lane)
        self.parts.append(vtx(cid, text, GW, rx - size // 2, ry - size // 2, size, size, parent))
        return cid

    def start(self, key, x, lane, y_off=0):
        rx, ry = self._rel_pos(x, lane, y_off)
        cid = uid(f"p{self.pi}")
        self.nodes[key] = cid
        parent = self._parent(lane)
        self.parts.append(vtx(cid, "", START, rx - 11, ry - 11, 22, 22, parent))
        return cid

    def end(self, key, x, lane, label="", y_off=0):
        rx, ry = self._rel_pos(x, lane, y_off)
        oid, iid = uid(f"p{self.pi}"), uid(f"p{self.pi}")
        self.nodes[key] = oid
        parent = self._parent(lane)
        self.parts.append(vtx(oid, label, END_OUTER, rx - 17, ry - 17, 34, 34, parent))
        self.parts.append(vtx(iid, "", END_INNER, rx - 7, ry - 7, 14, 14, parent))
        return oid

    def go(self, a, b, label="", dashed=False):
        self.parts.append(edg(uid(f"p{self.pi}e"), self.nodes[a], self.nodes[b], label, dashed))

    def draw_pool(self):
        n = len(self.lanes)
        pool_h = n * LANE_H
        xml = vtx(
            uid(f"p{self.pi}t"),
            self.title,
            "text;html=1;strokeColor=none;fillColor=none;align=center;fontStyle=1;"
            "fontSize=14;fontFamily=Helvetica;",
            ORIGIN_X,
            8,
            POOL_W,
            26,
        )
        xml += (
            f'        <mxCell id="{self.pool_id}" value="" style="{POOL}" '
            f'vertex="1" parent="1">'
            f'<mxGeometry x="{ORIGIN_X}" y="{ORIGIN_Y + 30}" width="{POOL_W}" '
            f'height="{pool_h}" as="geometry"/></mxCell>\n'
        )
        for i, name in enumerate(self.lanes):
            lid = self.lane_ids[i]
            xml += (
                f'        <mxCell id="{lid}" value="{esc(name)}" style="{LANE}" '
                f'vertex="1" parent="{self.pool_id}">'
                f'<mxGeometry y="{i * LANE_H}" width="{POOL_W}" height="{LANE_H}" '
                f'as="geometry"/></mxCell>\n'
            )
        return xml

    def render(self):
        body = self.draw_pool() + "".join(self.parts)
        pw = ORIGIN_X + POOL_W + 40
        ph = ORIGIN_Y + 30 + len(self.lanes) * LANE_H + 60
        return f"""  <diagram id="page-{self.pi}" name="{esc(self.title)}">
    <mxGraphModel dx="1400" dy="900" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="{pw}" pageHeight="{ph}" math="0" shadow="0">
      <root>
        <mxCell id="0"/>
        <mxCell id="1" parent="0"/>
{body}      </root>
    </mxGraphModel>
  </diagram>"""


def page_auth():
    L = ["Người dùng", "Ứng dụng Android", "Backend API", "Cơ sở dữ liệu"]
    g = SwimlanePage(1, "1. Đăng ký và đăng nhập", L)

    g.start("s", 70, 0)
    g.task("open", "Mở ứng dụng", 160, 0, w=120)
    g.gw("logged", "Đã đăng\nnhập?", 300, 1)
    g.task("main", "Vào\nMainActivity", 440, 1, w=120)
    g.end("e_ok", 580, 1)

    g.task("form", "Hiển thị form\nAuthActivity", 300, 1, w=130)
    g.gw("mode", "ĐK hay\nĐN?", 440, 0)
    g.task("reg_in", "Nhập thông tin\nđăng ký", 580, 0, w=140)
    g.task("login_in", "Nhập email\nvà mật khẩu", 580, 0, w=130, y_off=42)

    g.task("val", "Validate client\nAuthViewModel", 720, 1, w=155)
    g.gw("valid", "Hợp lệ?", 880, 1)
    g.task("err", "Hiển thị\nToast lỗi", 880, 0, w=120)
    g.gw("route", "ĐK hay\nĐN?", 1040, 2, y_off=0)

    g.task("reg_api", "POST\n/api/auth/register", 1180, 2, w=145, y_off=-22)
    g.gw("email", "Email\ntồn tại?", 1320, 2, y_off=-22)
    g.task("create", "INSERT user\nbcrypt hash", 1320, 3, w=130)

    g.task("login_api", "POST\n/api/auth/login", 1180, 2, w=130, y_off=28)
    g.gw("cred", "Đúng\nTK/MK?", 1320, 2, y_off=28)

    g.task("jwt", "Ký JWT\nsignToken", 1460, 2, w=110)
    g.task("session", "Lưu phiên\nSessionManager", 1460, 1, w=140)
    g.end("e_done", 1460, 0)

    g.go("s", "open")
    g.go("open", "logged")
    g.go("logged", "main", "Có")
    g.go("main", "e_ok")
    g.go("logged", "form", "Không")
    g.go("form", "mode")
    g.go("mode", "reg_in", "ĐK")
    g.go("mode", "login_in", "ĐN")
    g.go("reg_in", "val")
    g.go("login_in", "val")
    g.go("val", "valid")
    g.go("valid", "route", "Có")
    g.go("valid", "err", "Không")
    g.go("route", "reg_api", "ĐK")
    g.go("route", "login_api", "ĐN")
    g.go("reg_api", "email")
    g.go("email", "err", "Có")
    g.go("email", "create", "Không")
    g.go("create", "jwt")
    g.go("login_api", "cred")
    g.go("cred", "jwt", "Có")
    g.go("cred", "err", "Không")
    g.go("jwt", "session")
    g.go("session", "main")
    return g.render()


def page_destination():
    L = ["Người dùng", "Ứng dụng Android", "Backend API", "Cơ sở dữ liệu"]
    g = SwimlanePage(2, "2. Tìm kiếm và xem thông tin địa điểm", L)

    g.start("s", 60, 0)
    g.task("open", "Mở tab\nKhám phá / Trang chủ", 150, 0, w=155)
    g.task("load", "GET /api/destinations\noptionalAuth, phân trang", 300, 1, w=175)
    g.task("query", "Truy vấn\napp_places\n+ place_images", 300, 3, w=155)
    g.task("show", "Hiển thị\ndanh sách", 480, 1, w=130)

    g.gw("filter", "Tìm kiếm\n/lọc?", 620, 0)
    g.task("search", "Nhập từ khóa\n/chọn danh mục", 780, 0, w=155)
    g.gw("scroll", "Cuộn\ncuối?", 940, 0)
    g.task("more", "loadMore\npage++", 940, 1, w=120)
    g.task("tap", "Chọn\nđịa điểm", 1100, 0, w=110)
    g.task("detail", "GET /api/destinations/:id", 1100, 1, w=175)
    g.gw("found", "Tìm\nthấy?", 1280, 2)
    g.task("bind", "Hiển thị chi tiết\nảnh, mô tả, đánh giá", 1280, 1, w=165)
    g.task("err", "Thông báo\nlỗi", 1280, 0, w=110)
    g.end("e", 1440, 0)

    g.go("s", "open")
    g.go("open", "load")
    g.go("load", "query")
    g.go("query", "show")
    g.go("show", "filter")
    g.go("filter", "search", "Có")
    g.go("search", "load", "", True)
    g.go("filter", "scroll", "Không")
    g.go("scroll", "more", "Có")
    g.go("more", "load", "", True)
    g.go("scroll", "tap", "Không")
    g.go("tap", "detail")
    g.go("detail", "found")
    g.go("found", "bind", "Có")
    g.go("found", "err", "Không")
    g.go("bind", "e")
    return g.render()


def page_map():
    L = ["Người dùng", "Ứng dụng Android", "Backend API", "Dịch vụ ngoài"]
    g = SwimlanePage(3, "3. Xem bản đồ và định vị địa điểm", L)

    g.start("s", 60, 0)
    g.gw("entry", "Luồng\nnào?", 150, 0)
    # Luồng A: Gần bạn (Home)
    g.task("home", "Mở tab Trang chủ\nGần bạn", 300, 0, w=140, y_off=-28)
    g.gw("perm_h", "Cấp quyền\nvị trí?", 440, 0, y_off=-28)
    g.task("gps_h", "Fused Location\nGPS thiết bị", 440, 3, w=140, y_off=-28)
    g.task("nearby", "GET /api/destinations/nearby\nHaversine SQL", 580, 2, w=175, y_off=-28)
    g.task("list", "Hiển thị\ndanh sách gần bạn", 580, 1, w=145, y_off=-28)
    # Luồng B: Bản đồ chi tiết
    g.task("tap", "Chọn Xem bản đồ\ntừ chi tiết địa điểm", 300, 0, w=165, y_off=28)
    g.task("coords", "Nhận lat/lng/name\ntừ nav args", 460, 1, w=155, y_off=28)
    g.task("map", "MapFragment\nOSMDroid Mapnik", 620, 1, w=145, y_off=28)
    g.task("osm", "Tải tile\nOpenStreetMap", 620, 3, w=130, y_off=28)
    g.task("marker", "Gắn marker\nđịa điểm", 780, 1, w=130, y_off=28)

    g.gw("perm", "Cấp quyền\nvị trí?", 920, 0, y_off=28)
    g.task("gps", "Fused Location\nGPS thiết bị", 920, 3, w=140, y_off=28)
    g.task("here", "Marker\nBạn đang ở đây", 1080, 1, w=145, y_off=28)

    g.gw("dir", "Chỉ\nđường?", 1080, 0, y_off=28)
    g.task("route", "MapIntentHelper\nopenRoute / openPlace", 1240, 1, w=165, y_off=28)
    g.task("gmaps", "Mở\nGoogle Maps", 1240, 3, w=120, y_off=28)
    g.end("e", 1380, 0)

    g.go("s", "entry")
    g.go("entry", "home", "Gần bạn")
    g.go("entry", "tap", "Bản đồ")
    g.go("home", "perm_h")
    g.go("perm_h", "gps_h", "Có")
    g.go("perm_h", "nearby", "Không")
    g.go("gps_h", "nearby")
    g.go("nearby", "list")
    g.go("list", "e")
    g.go("tap", "coords")
    g.go("coords", "map")
    g.go("map", "osm")
    g.go("osm", "marker")
    g.go("marker", "perm")
    g.go("perm", "gps", "Có")
    g.go("perm", "here", "Không")
    g.go("gps", "here")
    g.go("here", "dir")
    g.go("dir", "route", "Có")
    g.go("dir", "e", "Không")
    g.go("route", "gmaps")
    g.go("gmaps", "e")
    return g.render()


def page_weather():
    L = ["Người dùng", "Ứng dụng Android", "Open-Meteo API"]
    g = SwimlanePage(4, "4. Xem dự báo thời tiết", L)

    g.start("s", 60, 0)
    g.task("open", "Mở chi tiết\nđịa điểm", 170, 0, w=130)
    g.task("load", "loadWeather(city)\nDestinationDetailFragment", 340, 1, w=195)
    g.task("lookup", "WeatherService\nmap cityCoords", 520, 1, w=155)
    g.gw("match", "Khớp\nthành phố?", 680, 1)
    g.task("default", "Dùng mặc định\nHà Nội", 680, 1, y_off=40, w=140)

    g.task("api", "GET /v1/forecast\n5 ngày", 840, 2, w=140)
    g.task("parse", "Parse JSON\nweather_code", 1000, 1, w=145)
    g.gw("ok", "Thành\ncông?", 1160, 1)
    g.task("show", "Hiển thị thẻ\nnhiệt độ, độ ẩm", 1160, 0, w=145)
    g.task("hide", "Ẩn cardWeather", 1160, 0, y_off=40, w=130)
    g.end("e", 1300, 0)

    g.go("s", "open")
    g.go("open", "load")
    g.go("load", "lookup")
    g.go("lookup", "match")
    g.go("match", "api", "Có")
    g.go("match", "default", "Không")
    g.go("default", "api")
    g.go("api", "parse")
    g.go("parse", "ok")
    g.go("ok", "show", "Có")
    g.go("ok", "hide", "Không")
    g.go("show", "e")
    g.go("hide", "e")
    return g.render()


def page_itinerary():
    L = ["Người dùng", "Ứng dụng Android", "Backend API", "Cơ sở dữ liệu"]
    g = SwimlanePage(5, "5. Tạo và quản lý lịch trình", L)

    g.start("s", 60, 0)
    g.task("open", "Mở tab\nLịch trình", 160, 0, w=120)
    g.task("list", "GET /api/itineraries\nJWT bắt buộc", 300, 1, w=165)
    g.task("show", "Hiển thị\ndanh sách", 460, 1, w=130)

    g.gw("act", "Thao tác?", 620, 0)
    g.task("create", "Tạo lịch trình\nCreateItineraryDialog", 760, 0, w=175)
    g.task("post", "POST /api/itineraries", 760, 2, w=155)
    g.task("days", "INSERT\nitinerary_days", 760, 3, w=140)

    g.task("view", "Xem chi tiết\nItineraryDetail", 920, 0, w=155)
    g.task("get", "GET /api/itineraries/:id", 920, 2, w=165)
    g.task("items", "Thêm/sửa/xóa\nitems & days", 1080, 1, w=155)
    g.task("save", "INSERT/UPDATE\nitinerary_items", 1080, 3, w=165)

    g.end("e", 1240, 0)

    g.go("s", "open")
    g.go("open", "list")
    g.go("list", "show")
    g.go("show", "act")
    g.go("act", "create", "Tạo")
    g.go("create", "post")
    g.go("post", "days")
    g.go("days", "list", "", True)
    g.go("act", "view", "Xem")
    g.go("view", "get")
    g.go("get", "items")
    g.go("items", "save")
    g.go("save", "e")
    return g.render()


def page_ai_itinerary():
    L = ["Người dùng", "Ứng dụng Android", "Backend API", "RAG/AI Service", "Cơ sở dữ liệu"]
    g = SwimlanePage(6, "6. Gợi ý lịch trình AI/RAG", L)

    g.start("s", 60, 0)
    g.task("open", "Mở tab\nLịch trình", 150, 0, w=120)
    g.task("ai_btn", "Bấm\nTạo tour AI", 280, 0, w=120)
    g.task("form", "Nhập title, tỉnh\nngày, budget, sở thích", 420, 0, w=175)
    g.task("val", "Validate form\nAIItineraryRequest", 420, 1, w=155)
    g.gw("valid", "Hợp lệ?", 580, 1)
    g.task("err", "Toast\nlỗi nhập liệu", 580, 0, w=110)

    g.task("api", "POST\n/api/ai/itinerary-options", 720, 2, w=175)
    g.task("rag", "Hybrid retrieve\n4 theme options", 720, 3, w=155)
    g.gw("opts", "Có\nphương án?", 880, 2)
    g.task("show", "Hiển thị 4 phương án\nAIItineraryOptions", 880, 1, w=175)
    g.task("pick", "Chọn phương án\nchỉnh sửa editor", 1040, 0, w=165)
    g.gw("sel", "Đã chọn\nđịa điểm?", 1040, 1)
    g.task("save", "POST\ncreate-from-option", 1200, 2, w=155)
    g.task("db", "INSERT\nitineraries + days\n+ items + place_id_map", 1200, 4, w=175)
    g.task("done", "Quay về\ndanh sách lịch trình", 1360, 1, w=155)
    g.end("e", 1360, 0)

    g.go("s", "open")
    g.go("open", "ai_btn")
    g.go("ai_btn", "form")
    g.go("form", "val")
    g.go("val", "valid")
    g.go("valid", "err", "Không")
    g.go("valid", "api", "Có")
    g.go("api", "rag")
    g.go("rag", "opts")
    g.go("opts", "err", "Không")
    g.go("opts", "show", "Có")
    g.go("show", "pick")
    g.go("pick", "sel")
    g.go("sel", "err", "Không")
    g.go("sel", "save", "Có")
    g.go("save", "db")
    g.go("db", "done")
    g.go("done", "e")
    return g.render()


def page_chatbot():
    L = ["Người dùng", "Ứng dụng Android", "Backend API", "RAG/Gemini Service"]
    g = SwimlanePage(7, "7. Quy trình Chatbot AI/RAG", L)

    g.start("s", 60, 0)
    g.task("open", "Mở tab\nChatbot", 150, 0, w=110)
    g.task("send", "Gửi tin nhắn\nChatbotFragment", 280, 0, w=130)
    g.task("prep", "prepareRagQuery\nPOST /api/ai/chat", 420, 1, w=165)
    g.task("gem1", "Gemini chuẩn hóa\ncâu hỏi + tỉnh/ngày", 420, 3, w=155)
    g.task("rag", "POST /api/ai/rag-chat\nproxy RAG", 580, 2, w=155)
    g.task("pipe", "RagPipeline\nretrieve + generate", 580, 3, w=155)
    g.gw("ok", "RAG\nthành công?", 740, 1)
    g.task("fb", "fallbackChat\nPOST /api/ai/chat", 740, 3, w=145)
    g.gw("prov", "Đúng\ntỉnh?", 900, 1)
    g.task("retry", "Retry strict\nprovince query", 900, 3, w=145)
    g.task("val", "validateRagOutput\nGemini kiểm tra", 1060, 1, w=155)
    g.gw("vok", "Hợp lệ?", 1060, 1, y_off=42)
    g.task("repair", "repairRagAnswer\nhoặc template", 1220, 3, w=155)
    g.task("show", "Hiển thị câu trả lời\n+ danh sách địa điểm", 1220, 0, w=175)
    g.gw("trip", "Tạo\nlịch trình?", 1380, 0)
    g.task("editor", "Navigate\nAIItineraryEditor", 1380, 1, w=145)
    g.end("e", 1380, 0, y_off=42)

    g.go("s", "open")
    g.go("open", "send")
    g.go("send", "prep")
    g.go("prep", "gem1")
    g.go("gem1", "rag")
    g.go("rag", "pipe")
    g.go("pipe", "ok")
    g.go("ok", "fb", "Không")
    g.go("ok", "prov", "Có")
    g.go("fb", "show")
    g.go("prov", "retry", "Không")
    g.go("retry", "val")
    g.go("prov", "val", "Có")
    g.go("val", "vok")
    g.go("vok", "retry", "Không")
    g.go("vok", "repair", "Có")
    g.go("repair", "show")
    g.go("show", "trip")
    g.go("trip", "editor", "Có")
    g.go("trip", "e", "Không")
    g.go("editor", "e")
    return g.render()


def page_reviews():
    L = ["Người dùng", "Ứng dụng Android", "Backend API", "Cơ sở dữ liệu", "Quản trị viên"]
    g = SwimlanePage(8, "8. Quy trình đánh giá địa điểm", L)

    g.start("s", 60, 0)
    g.task("open", "Mở chi tiết\nđịa điểm", 150, 0, w=130)
    g.gw("auth", "Đã đăng\nnhập?", 280, 1)
    g.task("login", "Yêu cầu\nđăng nhập", 280, 0, w=120)
    g.task("load", "GET /api/destinations\n/:id/reviews\nJWT bắt buộc", 420, 1, w=175)
    g.task("query", "SELECT reviews\nJOIN users", 420, 3, w=140)
    g.task("list", "Hiển thị\ndanh sách đánh giá", 580, 1, w=155)

    g.gw("act", "Viết\nđánh giá?", 740, 0)
    g.task("dlg", "ReviewDialog\nrating + comment + ảnh", 900, 0, w=165)
    g.gw("rate", "Đã chọn\nsao?", 900, 1)
    g.task("post", "POST /api/reviews\nJSON hoặc multipart", 1060, 2, w=175)
    g.gw("dest", "Địa điểm\ntồn tại?", 1060, 2, y_off=42)
    g.task("ins", "INSERT reviews\n+ cập nhật rating\ntrong app_places", 1220, 3, w=175)
    g.task("reload", "Reload\ndanh sách review", 1220, 1, w=140)

    g.task("admin", "Mở /admin/reviews\ntìm kiếm, sửa, xóa", 900, 4, w=165)
    g.task("mod", "POST save/delete\nrecalc aggregate", 1060, 4, w=155)
    g.end("e", 1380, 0)

    g.go("s", "open")
    g.go("open", "auth")
    g.go("auth", "login", "Không")
    g.go("auth", "load", "Có")
    g.go("load", "query")
    g.go("query", "list")
    g.go("list", "act")
    g.go("act", "dlg", "Có")
    g.go("act", "e", "Không")
    g.go("dlg", "rate")
    g.go("rate", "post", "Có")
    g.go("post", "dest")
    g.go("dest", "ins", "Có")
    g.go("ins", "reload")
    g.go("reload", "e")
    g.go("list", "admin", "", True)
    g.go("admin", "mod")
    g.go("mod", "query", "", True)
    return g.render()


def page_admin_data():
    L = ["Quản trị viên", "Trình duyệt Admin", "Backend API", "Cơ sở dữ liệu"]
    g = SwimlanePage(9, "9. Quy trình quản trị dữ liệu hệ thống", L)

    g.start("s", 60, 0)
    g.task("access", "Truy cập\n/admin", 160, 0, w=110)
    g.gw("auth", "Đã\nxác thực?", 300, 1)
    g.task("login", "Form đăng nhập\nPOST /admin/auth/login", 300, 0, w=175)
    g.task("cookie", "Set cookie\nadmin_session JWT", 440, 2, w=145)
    g.task("dash", "Dashboard\nthống kê users/places", 580, 1, w=155)

    g.gw("mod", "Module\nnào?", 740, 0)
    g.task("dest", "CRUD địa điểm\n/admin/destinations", 900, 0, w=165, y_off=-22)
    g.task("users", "CRUD người dùng\n/admin/users", 900, 0, w=155, y_off=22)
    g.task("rev", "Quản lý đánh giá\n/admin/reviews", 1060, 0, w=155, y_off=-22)
    g.task("sys", "Xem hệ thống\n/admin/system", 1060, 0, w=145, y_off=22)

    g.gw("crud", "Thao tác?", 1220, 1)
    g.task("save", "POST save\nvalidate + bcrypt", 1220, 2, w=145)
    g.task("db", "INSERT/UPDATE/DELETE\napp_places, users, reviews", 1220, 3, w=175)
    g.task("ok", "Reload trang\nthông báo kết quả", 1380, 1, w=155)
    g.end("e", 1380, 0)

    g.go("s", "access")
    g.go("access", "auth")
    g.go("auth", "login", "Không")
    g.go("login", "cookie")
    g.go("cookie", "dash")
    g.go("auth", "dash", "Có")
    g.go("dash", "mod")
    g.go("mod", "dest", "Địa điểm")
    g.go("mod", "users", "User")
    g.go("mod", "rev", "Review")
    g.go("mod", "sys", "System")
    g.go("dest", "crud")
    g.go("users", "crud")
    g.go("rev", "crud")
    g.go("sys", "e")
    g.go("crud", "save", "Ghi")
    g.go("save", "db")
    g.go("db", "ok")
    g.go("ok", "e")
    return g.render()


def page_admin_rag():
    L = ["Quản trị viên", "Trình duyệt Admin", "Backend API", "RAG Service"]
    g = SwimlanePage(10, "10. Quy trình Admin giám sát AI/RAG", L)

    g.start("s", 60, 0)
    g.task("open", "Mở\n/admin/rag-ai", 160, 0, w=120)
    g.task("fetch", "Gọi song song 5 API\noverview, status, self-test\nmetrics, data-quality", 340, 1, w=195)
    g.task("rag5", "FastAPI admin\nendpoints", 340, 3, w=155)
    g.task("dash", "Hiển thị dashboard\nRAG ready, files, cache", 520, 1, w=175)

    g.gw("act", "Thao tác\nvận hành?", 680, 0)
    g.task("reload", "Reload\nPlace Store", 840, 0, w=130, y_off=-35)
    g.task("cache", "Clear\nCache", 840, 0, w=110, y_off=0)
    g.task("debug", "Debug Query\ncâu hỏi test RAG", 840, 0, w=145, y_off=35)
    g.task("logs", "Xem AI Logs\nvà metrics", 1000, 0, w=130)

    g.task("proxy", "Proxy POST/GET\nfetchRagJson", 1000, 2, w=145)
    g.gw("ok", "RAG\nphản hồi OK?", 1160, 2)
    g.task("show", "Hiển thị JSON\nkết quả / lỗi 502", 1160, 1, w=155)
    g.end("e", 1320, 0)

    g.go("s", "open")
    g.go("open", "fetch")
    g.go("fetch", "rag5")
    g.go("rag5", "dash")
    g.go("dash", "act")
    g.go("act", "reload", "Reload")
    g.go("act", "cache", "Cache")
    g.go("act", "debug", "Debug")
    g.go("act", "logs", "Logs")
    g.go("reload", "proxy")
    g.go("cache", "proxy")
    g.go("debug", "proxy")
    g.go("logs", "proxy")
    g.go("proxy", "ok")
    g.go("ok", "show", "Có")
    g.go("ok", "show", "Không")
    g.go("show", "e")
    return g.render()


def validate(path):
    ET.parse(path)
    with open(path, encoding="utf-8") as f:
        text = f.read()
    ids = re.findall(r'id="([^"]+)"', text)
    seen, dupes = set(), set()
    for i in ids:
        if i in ("0", "1"):
            continue
        if i in seen:
            dupes.add(i)
        seen.add(i)
    if dupes:
        raise ValueError(f"Duplicate IDs: {sorted(dupes)[:10]}")
    print(f"OK – {len(seen)} unique IDs, XML valid")


def main():
    global _gid
    _gid = 0
    pages = [
        page_auth(),
        page_destination(),
        page_map(),
        page_weather(),
        page_itinerary(),
        page_ai_itinerary(),
        page_chatbot(),
        page_reviews(),
        page_admin_data(),
        page_admin_rag(),
    ]
    content = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<mxfile host="app.diagrams.net" modified="2026-05-21T20:00:00.000Z" '
        'agent="UNUtrip" version="22.1.0" type="device" pages="10">\n'
        + "\n".join(pages)
        + "\n</mxfile>\n"
    )
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(content)
    validate(OUT)
    print(f"Written: {OUT}")


if __name__ == "__main__":
    main()
