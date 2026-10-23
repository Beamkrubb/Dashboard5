"""
Source registry for D01–D10 (mirrors handoff_n.md).

Each Resource is one downloadable file. `auto=True` means scripts/download_data.py
fetches it; `auto=False` means the portal blocks automation and the file must be
downloaded in a browser and saved to `data/raw/<dataset_id>/<filename>`.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

OAE = "https://catalog.oae.go.th/dataset"
LDD = "https://lddcatalog.ldd.go.th/dataset/ff8c5f01-853b-4165-88fe-d9691de2b400/resource"


@dataclass
class Resource:
    filename: str
    url: str
    auto: bool = True
    crop: Optional[str] = None
    note: str = ""


@dataclass
class Dataset:
    id: str
    name_th: str
    owner: str
    status: str            # ok | partial | substitute
    page: str
    license: str
    resources: List[Resource] = field(default_factory=list)
    manual_steps: str = ""


DATASETS: List[Dataset] = [
    Dataset(
        "D01", "สถิติการผลิตสินค้าเกษตรรายปี", "สศก.", "ok",
        "https://catalog.oae.go.th/group/production", "OAE open data",
        [
            Resource("cassava_production_province.csv",
                     f"{OAE}/5b3ab1a4-dc21-4d99-b476-709923203e0d/resource/13dbdafd-7a1f-421c-aff2-94f0b68d8a46/download/cassava_production_province-1.csv",
                     crop="cassava"),
            Resource("maize_totalcrop_product_province.csv",
                     f"{OAE}/a80e842d-1e48-4b32-bdc5-27df3e47dbff/resource/3dfb84c0-2443-4f07-84c8-cde942974c16/download/maize_totalcrop_product_province.csv",
                     crop="maize"),
            Resource("para_rubber_production_province.xlsx",
                     f"{OAE}/a0072a36-170d-4505-b8f1-de6d467c5f1b/resource/99f647d5-8944-4847-99ce-61ef210efa96/download/para_rubber_production_province.xlsx",
                     crop="rubber"),
            Resource("oil_palm_production_province.xlsx",
                     f"{OAE}/c10379a2-791b-44ae-87a0-53355a99be1b/resource/65e0ccac-87ac-4a4d-9eb7-5611cccd78c6/download/oil_palm_production_province.xlsx",
                     crop="oil_palm"),
        ],
        manual_steps=("Rice 2550–2562 and the remaining crops: open the OAE production group in a browser "
                      "(pages 1–3), download each *ระดับจังหวัด* file into data/raw/D01/, and name it "
                      "<crop>_production_province.<ext>. Rice history: extract the province tables from "
                      "'สถิติการเกษตรของประเทศไทย' PDFs into data/raw/D01/rice_production_province.csv."),
    ),
    Dataset(
        "D02", "สถิติราคาหน้าไร่นารายสัปดาห์", "สศก. / NABC", "partial",
        "https://catalog.oae.go.th/group/price", "OAE open data",
        [],  # filled dynamically from WEEKLY_PRICE_PRODUCTS by the downloader (paginated JSON API)
        manual_steps="If the API has no 2018–2019 weeks, download monthly_prices_<crop> from OAE instead.",
    ),
    Dataset(
        "D03", "สถิติต้นทุนการผลิตและเครื่องจักรกล", "สศก. (substitute: NSO)", "substitute",
        "https://catalog.nso.go.th/en/dataset/0506_11_0001", "CC BY (NSO)",
        [Resource("logistics_cost_rice.pdf", "https://catalog.oae.go.th/dataset/logis-rice", auto=False)],
        manual_steps=("No national cost CSV exists. Enter cost per rai for main crops 2561–2562 from OAE "
                      "publications into data/raw/D03/production_cost_manual.csv with columns "
                      "crop,year_be,cost_baht_per_rai,cost_baht_per_kg,source_url. Never estimate values."),
    ),
    Dataset(
        "D04", "สถิติพื้นที่ชลประทานรายจังหวัด", "กรมชลประทาน & สศก.", "substitute",
        "https://www.rid.go.th", "RID publication",
        [Resource("rid_annual_2566.pdf",
                  "https://www.rid.go.th/_data/documents/rid_annual_conclusion/02_conclusion/2566/Booklet.pdf",
                  note="annual report; province table must be extracted")],
        manual_steps=("Extract irrigated area by province (rai) into data/raw/D04/irrigated_area_province.csv "
                      "with columns province,year_be,irrigated_area_rai,source_url (pdfplumber helper: "
                      "scripts/extract_pdf_tables.py)."),
    ),
    Dataset(
        "D05", "ความเหมาะสมของดิน Agri-Map (Zoning)", "กรมพัฒนาที่ดิน", "ok",
        "https://lddcatalog.ldd.go.th/en/dataset/lpd", "CC BY-ND",
        [
            Resource("datadict_zoning.csv", f"{LDD}/626f7b83-dfd3-4d30-a2a7-aaa18fe00cd5/download/datadict_zoning.csv"),
            Resource("areazoning_rice.csv", f"{LDD}/7f508d88-3c31-4cad-b95a-68ca0ce89356/download/areazoning_rice.csv", crop="rice"),
            Resource("areazoning_cassava.csv", f"{LDD}/7312af9d-8286-4527-85e1-c505c8bc75db/download/areazoning_cassava.csv", crop="cassava"),
            Resource("areazoning_maize.csv", f"{LDD}/08ddd54d-8fab-49b5-89d0-3f472149b5df/download/areazoning_maize.csv", crop="maize"),
            Resource("areazoning_sugarcane.csv", f"{LDD}/49acd299-bc4a-482d-9fe4-b5d81c643758/download/areazoning_sugarcane.csv", crop="sugarcane"),
            Resource("areazoning_rubber.csv", f"{LDD}/a1c2b391-30aa-4d23-a110-4e30c1bb7e28/download/areazoning_rubber.csv", crop="rubber"),
            Resource("areazoning_plam.csv", f"{LDD}/ab6db1dc-648e-44f6-8ede-09c2bd5a02b8/download/areazoning_plam.csv", crop="oil_palm"),
            Resource("areazoning_pineapple.csv", f"{LDD}/31e5b015-cb6a-4fd1-b3c8-34d6bfc6be8d/download/areazoning_pineapple.csv", crop="pineapple"),
            Resource("areazoning_longan.csv", f"{LDD}/dd7cb483-b239-49d3-a73c-45a6a1657f8e/download/areazoning_longan.csv", crop="longan"),
            Resource("areazoning_rambutan.csv", f"{LDD}/5ffb923e-c71c-428d-ac84-259f4fc6ab18/download/areazoning_rambutan.csv", crop="rambutan"),
            Resource("areazoning_durian.csv", f"{LDD}/c45a0a57-c9e5-4aff-a3e4-410cf4a39240/download/areazoning_durian.csv", crop="durian"),
            Resource("areazoning_mangosteen.csv", f"{LDD}/f8d772b0-5b95-43d2-9045-a3c95f5e22d2/download/areazoning_mangosteen.csv", crop="mangosteen"),
            Resource("areazoning_coconut.csv", f"{LDD}/d6956088-a2ce-407d-b111-84d8a45367f8/download/areazoning_coconut.csv", crop="coconut"),
            Resource("areazoning_robusta.csv", f"{LDD}/6bb696e0-27b8-4945-80c0-371c0faafb53/download/areazoning_robusta.csv", crop="coffee_robusta"),
            Resource("areazoning_arabica.csv", f"{LDD}/049a14b4-d6d0-4eda-b454-61d3d692f9ed/download/areazoning_arabica.csv", crop="coffee_arabica"),
        ],
    ),
    Dataset(
        "D06", "พื้นที่เกษตรประสบภัยพิบัติ", "ปภ. (substitute for DOAE)", "substitute",
        "https://catalog.disaster.go.th/en/dataset/dpm-gd027", "Open Data Common",
        [
            Resource("flood_stats.zip", "https://drive.disaster.go.th/index.php/s/kd55qos3To6D4Cx/download", auto=False),
            Resource("windstorm_stats.zip", "https://drive.disaster.go.th/index.php/s/bbmZcMzMaXMozdB/download", auto=False),
        ],
        manual_steps=("Download yearly CSV/XLSX for dpm-gd027 (flood), dpm-gd028 (drought), dpm-gd030 (windstorm) "
                      "into data/raw/D06/ as <hazard>_<year_be>.csv|xlsx."),
    ),
    Dataset(
        "D07", "ฝนเชิงพื้นที่รายจังหวัด (IDW)", "สสน.", "partial",
        "https://data.go.th/dataset/spatial-rain", "CC BY-NC",
        [Resource("spatial_rain.csv", "https://data.go.th/dataset/spatial-rain", auto=False),
         Resource("tmax_tmin.csv", "https://data.go.th/dataset/tmax-tmin", auto=False)],
        manual_steps=("data.go.th download links render only in a browser: save the CSVs as "
                      "data/raw/D07/spatial_rain.csv and data/raw/D07/tmax_tmin.csv. "
                      "2018 (B.E. 2561) gap is filled by Open-Meteo (auto, labelled as ERA5)."),
    ),
    Dataset(
        "D08", "ฝนสะสมเฉลี่ยประเทศระยะยาว", "substitute: CRU via World Bank CCKP / ERA5", "substitute",
        "https://climateknowledgeportal.worldbank.org/country/thailand/climate-data-historical", "CC BY 4.0 (CCKP)",
        [Resource("cckp_thailand_annual_precip.csv",
                  "https://climateknowledgeportal.worldbank.org/country/thailand/climate-data-historical", auto=False)],
        manual_steps=("Download the annual precipitation series (CRU) for Thailand from CCKP Data Download "
                      "and save as data/raw/D08/cckp_thailand_annual_precip.csv. If unavailable, the "
                      "downloader builds an ERA5 national mean from province centroids (flag --era5-longterm)."),
    ),
    Dataset(
        "D09", "ข้อมูลตรวจวัดอุตุนิยมวิทยา", "TMD", "partial",
        "https://data.tmd.go.th/api/index1.php", "TMD registration",
        [],
        manual_steps="Set TMD_UID / TMD_UKEY environment variables (register at data.tmd.go.th) to enable the cache.",
    ),
    Dataset(
        "D10", "ขอบเขตจังหวัด", "OpenGISData-Thailand", "ok",
        "https://github.com/chingchai/OpenGISData-Thailand", "not stated – attribute source",
        [Resource("provinces.geojson",
                  "https://raw.githubusercontent.com/chingchai/OpenGISData-Thailand/master/provinces.geojson")],
    ),
]

# D02 weekly price products (NABC API product_name values listed in OAE catalog resources).
NABC_WEEKLY_URL = "https://agriapi.nabc.go.th/api/weekly-prices/product"
WEEKLY_PRICE_PRODUCTS = {
    "rice_hommali": "ข้าวเปลือกเจ้าหอมมะลิ ความชื้น 15",
    "rice_white": "ข้าวเปลือกเจ้า ความชื้น 15",
    "rice_glutinous": "ข้าวเปลือกเหนียวนาปียาว ความชื้น 15",
    # Add more from catalog.oae.go.th/dataset/weekly_price_<crop> (check exact product_name strings).
}

OPEN_METEO_ARCHIVE = "https://archive-api.open-meteo.com/v1/archive"
TMD_BASE = "https://data.tmd.go.th/api"


def get(dataset_id: str) -> Dataset:
    for d in DATASETS:
        if d.id == dataset_id:
            return d
    raise KeyError(dataset_id)
