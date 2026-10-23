# Handoff: แหล่งข้อมูลเปิดสำหรับ Dashboard เกษตรไทย

สรุปแหล่งข้อมูลจริง สถานะการเข้าถึง และแหล่งทดแทน สำหรับส่งต่อให้ AI/ผู้พัฒนารายถัดไป · ตรวจลิงก์เมื่อ 23 ต.ค. 2569 (2026-10-23)

## ภารกิจ
เป้าหมาย: สร้าง interactive dashboard เกษตรรายจังหวัดของไทย (77 จังหวัด) ที่เชื่อมผลผลิต ราคา ต้นทุน ชลประทาน ความเหมาะสมของดิน ภัยพิบัติ และฝน เข้ากับแผนที่ขอบเขตจังหวัด

ขั้นตอนที่แนะนำ:
1) ดาวน์โหลดไฟล์จากลิงก์ "แหล่งหลัก" ของแต่ละชุด (ถ้าสถานะเป็น "ใช้แหล่งทดแทน" ให้ใช้รายการ "แหล่งทดแทน")
2) แปลงทุกตารางเป็นรูปแบบ long/tidy ตามสคีมาด้านล่าง เก็บไว้ที่ data/clean/*.csv
3) ทำตารางอ้างอิงจังหวัด (province_lookup.csv) จาก GeoJSON แล้ว join ทุกชุดด้วย pro_code
4) สร้าง dashboard เป็นไฟล์ HTML เดียว (แผนที่ choropleth + กราฟแนวโน้ม + ตัวกรองปี/พืช/จังหวัด)
5) อัปเดตช่อง "สถานะ" และ "หมายเหตุ" ในไฟล์นี้เมื่อพบปัญหาใหม่

## ชุดข้อมูล

### D01 สถิติการผลิตสินค้าเกษตรรายปี  [ใช้ได้]
- เจ้าของ: สำนักงานเศรษฐกิจการเกษตร (สศก.)
- รูปแบบ/ขอบเขตที่ต้องการ: Excel / CSV | 77 จังหวัด, 26 ชนิดพืช (2550–2562)
- License: เปิดเผย (ตรวจ license รายชุดใน catalog)
- Join key: ชื่อจังหวัด (ไทย) → map เป็น pro_code
- สิ่งที่พบ: OAE Catalog มีชุด 'ปริมาณการผลิต' รายพืช แยกระดับประเทศ/ภาค/จังหวัด ย้อนหลังยาว (เช่น มันสำปะหลัง 2523–2568, ข้าวโพด 2527–2567, ยาง 2531–2567, ปาล์ม 2525–2567) ครอบคลุมช่วง 2550–2562 ได้ หมวดผลผลิตมีทั้งหมด 70 ชุด
- แหล่งหลัก:
  - [OAE Catalog – หมวดปริมาณการผลิต (70 ชุด)](https://catalog.oae.go.th/group/production) — เปิดในเบราว์เซอร์เพื่อดูหน้า 2–3
  - [มันสำปะหลังโรงงาน ระดับจังหวัด (CSV, 2523–2568)](https://catalog.oae.go.th/dataset/5b3ab1a4-dc21-4d99-b476-709923203e0d/resource/13dbdafd-7a1f-421c-aff2-94f0b68d8a46/download/cassava_production_province-1.csv) — dataset: dataoae1304
  - [ข้าวโพดเลี้ยงสัตว์ ทั้งปี ระดับจังหวัด (CSV, 2527–2567)](https://catalog.oae.go.th/dataset/a80e842d-1e48-4b32-bdc5-27df3e47dbff/resource/3dfb84c0-2443-4f07-84c8-cde942974c16/download/maize_totalcrop_product_province.csv) — dataset: dataoae1204 (มีแยกรุ่น 1/รุ่น 2 ด้วย)
  - [ยางพารา ระดับจังหวัด (XLSX, 2531–2567)](https://catalog.oae.go.th/dataset/a0072a36-170d-4505-b8f1-de6d467c5f1b/resource/99f647d5-8944-4847-99ce-61ef210efa96/download/para_rubber_production_province.xlsx) — dataset: dataoae1404
  - [ปาล์มน้ำมัน ระดับจังหวัด (XLSX, 2525–2567)](https://catalog.oae.go.th/dataset/c10379a2-791b-44ae-87a0-53355a99be1b/resource/65e0ccac-87ac-4a4d-9eb7-5611cccd78c6/download/oil_palm_production_province.xlsx) — dataset: dataoae1504
  - [ข้าว (นาปี/นาปรัง) – dataoae1104](https://catalog.oae.go.th/dataset/dataoae1104) — CSV มีเฉพาะ 2563–2568 + PDF 2565–2568 → ช่วง 2550–2562 ต้องใช้แหล่งทดแทน
- แหล่งทดแทน:
  - [สถิติการเกษตรของประเทศไทย (หนังสือรายปี สศก.)](https://prt.parliament.go.th/items/b6d507fb-a2b8-4a9b-803b-8019fa0fc1bf) — ตารางรายจังหวัดของข้าวย้อนหลัง (PDF ต้องสกัดตาราง)
  - [NSO Statistical Yearbook ตาราง 11.3 เนื้อที่ใช้ประโยชน์ทางการเกษตรรายจังหวัด](https://www.nso.go.th/public/e-book/Statistical-Yearbook/SYB-2025_webPage/File%20SYB/2025/11/T%2011.3%202025.pdf) — แหล่งข้อมูลคือ สศก.; ปีอื่นเปลี่ยนเลขปีใน URL
- หมายเหตุ: ยังไม่ได้ยืนยันว่าครบ 26 ชนิดพืช — ต้องไล่ดูรายการทั้ง 70 ชุดในหมวดผลผลิต (ชุด *_product_month / *_plant_month เป็นร้อยละรายเดือน ไม่ใช่ผลผลิตรายปี). slug รูปแบบ dataoaeXX04 ใช้กับพืชหลัก. ระวัง metadata 'ปีล่าสุด 2565' ไม่ตรงกับไฟล์

### D02 สถิติราคาหน้าไร่นารายสัปดาห์  [ได้บางส่วน]
- เจ้าของ: สำนักงานเศรษฐกิจการเกษตร (สศก.)
- รูปแบบ/ขอบเขตที่ต้องการ: CSV | รายสัปดาห์ ครอบคลุมพืชเศรษฐกิจ (2561–2562)
- License: เปิดเผย
- Join key: ราคาระดับประเทศ (ไม่ใช่รายจังหวัด) → join ด้วย year/week + crop
- สิ่งที่พบ: OAE Catalog หมวดราคามี 16 ชุด 'ราคาที่เกษตรกรขายได้รายสัปดาห์' (ข้าวเปลือก ข้าวโพด มันสำปะหลัง ยาง ปาล์ม มะพร้าว ลำไย สับปะรด พริกไทย และปศุสัตว์) แต่ resource เป็น JSON API ของ NABC ไม่ใช่ CSV และยังไม่ยืนยันว่ามีย้อนถึง 2561
- แหล่งหลัก:
  - [OAE Catalog – หมวดราคา (35 ชุด)](https://catalog.oae.go.th/group/price) — slug weekly_price_<crop>
  - [ตัวอย่าง: weekly_price_rice](https://catalog.oae.go.th/dataset/weekly_price_rice) — 3 resource: หอมมะลิ, ข้าวเจ้า, ข้าวเหนียว (ความชื้น 15%)
  - [NABC Agri API – weekly prices (JSON, แบ่งหน้า)](https://agriapi.nabc.go.th/api/weekly-prices/product?product_name=ข้าวเปลือกเจ้าหอมมะลิ%20ความชื้น%2015&page=1) — วน page=1..N จนหมด แล้วแปลงเป็น CSV
- แหล่งทดแทน:
  - [ราคารายเดือน monthly_prices_<crop> (OAE)](https://catalog.oae.go.th/dataset/monthly_prices_rice) — ใช้แทนถ้า API รายสัปดาห์ไม่มีปี 2561–2562
- หมายเหตุ: งานแรกที่ต้องทำ: เรียก API ดูว่ามีข้อมูลเริ่มปีใด และฟิลด์อะไรบ้าง. รายชื่อ weekly: rice, maize, cassava, rubber, oil-plam, coconut, longen, pineapples, black-pepper, beef, buffaloes, broiler-chicken, swine, egg, vannamei_shrimp, milk (สะกดตาม slug จริง). หมายเหตุ: คำอธิบายของ weekly_price_black-pepper ใน catalog เขียนเป็นมะพร้าว — ตรวจข้อมูลจริง

### D03 สถิติต้นทุนการผลิตและเครื่องจักรกล  [ใช้แหล่งทดแทน]
- เจ้าของ: สำนักงานเศรษฐกิจการเกษตร (สศก.)
- รูปแบบ/ขอบเขตที่ต้องการ: CSV | พืชเศรษฐกิจหลัก (2561–2562)
- License: ตามแต่ละแหล่ง
- Join key: crop + year (ส่วนใหญ่เป็นระดับประเทศ)
- สิ่งที่พบ: ไม่พบชุดต้นทุนการผลิตระดับประเทศของ สศก. ในรูป CSV บน OAE Catalog (ค้นคำว่า 'ต้นทุน' พบเพียงต้นทุนโลจิสติกส์ข้าว/ยาง/ปาล์ม เป็น PDF). บน data.go.th มีแต่ชุดรายจังหวัดย่อย ๆ
- แหล่งหลัก:
  - [ต้นทุนโลจิสติกส์ข้าว (OAE)](https://catalog.oae.go.th/dataset/logis-rice) — PDF; มีชุด logis-rubber, logis-plam ด้วย
- แหล่งทดแทน:
  - [สำมะโนการเกษตร 2566 (สสช.) – XLSX](https://catalog.nso.go.th/en/dataset/0506_11_0001) — ใช้ดูการถือครอง/การใช้เครื่องจักรกล (ตรวจว่ามีตารางเครื่องจักรรายจังหวัดหรือไม่)
  - [ตัวอย่างชุดต้นทุนรายจังหวัดบน data.go.th](https://data.go.th/en/dataset/skn_doae_01003) — ต้นทุนข้าวเฉลี่ยต่อไร่ (จังหวัดเดียว) — ใช้ได้เฉพาะเป็นตัวอย่าง
  - [เว็บไซต์ สศก. (ตารางต้นทุนการผลิต)](https://www.oae.go.th) — หน้าเว็บ render ด้วย JS ดึงอัตโนมัติไม่ได้ ต้องเปิดเบราว์เซอร์หาเมนู 'ต้นทุนการผลิตสินค้าเกษตร'
- หมายเหตุ: ทางเลือกสุดท้าย: กรอกต้นทุนต่อไร่ของพืชหลัก (ข้าวนาปี, ข้าวนาปรัง, มันสำปะหลัง, ข้าวโพดเลี้ยงสัตว์, อ้อย, ยาง, ปาล์ม) ปี 2561–2562 ด้วยมือจากเอกสาร สศก. แล้วบันทึกที่มาเป็นรายแถว. อย่าเดาตัวเลข

### D04 สถิติพื้นที่ชลประทานรายจังหวัด  [ใช้แหล่งทดแทน]
- เจ้าของ: กรมชลประทาน & สศก.
- รูปแบบ/ขอบเขตที่ต้องการ: CSV | 77 จังหวัด (2561–2562)
- License: ตามแต่ละแหล่ง
- Join key: ชื่อจังหวัด → pro_code
- สิ่งที่พบ: ไม่พบ CSV ระดับประเทศแยกรายจังหวัดจากกรมชลประทานบน open data portal ที่เปิดได้. data.go.th มีเฉพาะชุดของสำนักงานจังหวัดบางจังหวัด
- แหล่งหลัก:
  - [รายงานสรุปผลงานประจำปี กรมชลประทาน (PDF)](https://www.rid.go.th/_data/documents/rid_annual_conclusion/02_conclusion/2566/Booklet.pdf) — ปีอื่น: เปลี่ยน 2566 เป็น 2562/2564/2565 (ไฟล์ 2562 ชื่อ แผ่นพับ.pdf)
- แหล่งทดแทน:
  - [สถิติการเกษตรของประเทศไทย (สศก.) – ตารางเนื้อที่ชลประทานรายจังหวัด](https://prt.parliament.go.th/items/b6d507fb-a2b8-4a9b-803b-8019fa0fc1bf) — PDF ต้องสกัดตาราง
  - [พื้นที่ทำเกษตรในเขตชลประทาน (data.go.th)](https://data.go.th/en/dataset/dataset_10_078) — ระดับจังหวัดเดียว — ใช้ตรวจความสมเหตุสมผล
  - [พื้นที่แล้งซ้ำซาก (LDD) – สถิติรายตำบล CSV](https://lddcatalog.ldd.go.th/dataset/f2ea827d-8b8b-4de6-9fa9-acc73dea1278/resource/b394ac5a-03be-4673-9a42-beafd3117e35/download/csv.csv) — ใช้พื้นที่ชลประทานเป็นปัจจัยวิเคราะห์ ใช้เป็นตัวชี้วัดความเสี่ยงน้ำแทนได้; CC BY-NC-ND
- หมายเหตุ: ต้องสกัดตารางจาก PDF (pdfplumber/camelot). ระบุชัดใน dashboard ว่าตัวเลขมาจากเอกสาร PDF

### D05 ความเหมาะสมของดินตามระบบ Agri-Map  [ใช้ได้]
- เจ้าของ: กรมพัฒนาที่ดิน (LDD)
- รูปแบบ/ขอบเขตที่ต้องการ: CSV | 77 จังหวัด (S1, S2, S3, N)
- License: CC BY-ND (ห้ามดัดแปลงเนื้อหาต้นฉบับ — แสดงผล/อ้างอิงได้)
- Join key: ชื่อจังหวัด → pro_code
- สิ่งที่พบ: LDD Catalog ชุด 'เขตความเหมาะสมของที่ดินสำหรับการปลูกพืชเศรษฐกิจ (Zoning)' มี CSV สถิติรายจังหวัดแยก S1/S2/S3/N ครบ 13 พืช + Shapefile + data dictionary. อัปเดตล่าสุด 7 ต.ค. 2568
- แหล่งหลัก:
  - [หน้า dataset (LDD Catalog: lpd)](https://lddcatalog.ldd.go.th/en/dataset/lpd) — 13 พืช: ข้าว ข้าวโพด มันสำปะหลัง อ้อย สับปะรด ยาง ปาล์ม มะพร้าว กาแฟโรบัสตา/อาราบิกา ลำไย เงาะ มังคุด ทุเรียน
  - [ข้าว – สถิติรายจังหวัด (CSV)](https://lddcatalog.ldd.go.th/dataset/ff8c5f01-853b-4165-88fe-d9691de2b400/resource/7f508d88-3c31-4cad-b95a-68ca0ce89356/download/areazoning_rice.csv)
  - [มันสำปะหลัง (CSV)](https://lddcatalog.ldd.go.th/dataset/ff8c5f01-853b-4165-88fe-d9691de2b400/resource/7312af9d-8286-4527-85e1-c505c8bc75db/download/areazoning_cassava.csv)
  - [ข้าวโพด (CSV)](https://lddcatalog.ldd.go.th/dataset/ff8c5f01-853b-4165-88fe-d9691de2b400/resource/08ddd54d-8fab-49b5-89d0-3f472149b5df/download/areazoning_maize.csv)
  - [อ้อย (CSV)](https://lddcatalog.ldd.go.th/dataset/ff8c5f01-853b-4165-88fe-d9691de2b400/resource/49acd299-bc4a-482d-9fe4-b5d81c643758/download/areazoning_sugarcane.csv)
  - [ยางพารา (CSV)](https://lddcatalog.ldd.go.th/dataset/ff8c5f01-853b-4165-88fe-d9691de2b400/resource/a1c2b391-30aa-4d23-a110-4e30c1bb7e28/download/areazoning_rubber.csv)
  - [ปาล์มน้ำมัน (CSV)](https://lddcatalog.ldd.go.th/dataset/ff8c5f01-853b-4165-88fe-d9691de2b400/resource/ab6db1dc-648e-44f6-8ede-09c2bd5a02b8/download/areazoning_plam.csv)
  - [Data dictionary (CSV)](https://lddcatalog.ldd.go.th/dataset/ff8c5f01-853b-4165-88fe-d9691de2b400/resource/626f7b83-dfd3-4d30-a2a7-aaa18fe00cd5/download/datadict_zoning.csv) — อ่านก่อนเพื่อรู้ชื่อคอลัมน์
- แหล่งทดแทน:
  - [Shapefile Zoning (ไฟล์ .rar)](https://tswc.ldd.go.th/DownloadGIS/Index_Zoning.html) — ใช้เมื่อต้องการแผนที่ละเอียดระดับพื้นที่
- หมายเหตุ: ลิงก์ CSV พืชอื่น (สับปะรด ลำไย เงาะ ทุเรียน มังคุด มะพร้าว กาแฟ) อยู่ในหน้า dataset lpd. ข้อมูลเป็นภาพตัดขวาง (ไม่มีมิติปี)

### D06 รายงานพื้นที่เกษตรประสบภัยพิบัติ  [ใช้แหล่งทดแทน]
- เจ้าของ: กรมส่งเสริมการเกษตร (DOAE) & ปภ.
- รูปแบบ/ขอบเขตที่ต้องการ: CSV | 77 จังหวัด (2561–2562)
- License: Open Data Common (ปภ.)
- Join key: ชื่อจังหวัด → pro_code
- สิ่งที่พบ: ระบบรายงานของ DOAE (disaster.doae.go.th) ต้องล็อกอิน ThaiD. ชุดบน data.go.th (disaster3) มีเพียงปี 2567. ปภ. มี catalog เปิดพร้อมสถิติอุทกภัย/ภัยแล้ง/วาตภัยรายปี 2562–2567 (XLSX/CSV) ที่มีหมวดความเสียหายด้านการเกษตร
- แหล่งหลัก:
  - [ปภ. – สถิติรายปีการเกิดอุทกภัย (dpm-gd027)](https://catalog.disaster.go.th/en/dataset/dpm-gd027) — 2562–2567; ไฟล์รวมที่ drive.disaster.go.th/index.php/s/kd55qos3To6D4Cx
  - [ปภ. – สถิติรายปีการเกิดภัยแล้ง (dpm-gd028)](https://catalog.disaster.go.th/en/dataset/dpm-gd028) — 2562–2568
  - [ปภ. – สถิติรายปีการเกิดวาตภัย (dpm-gd030)](https://catalog.disaster.go.th/en/dataset/dpm-gd030) — หน่วยข้อมูลรายจังหวัด; ไฟล์ที่ drive.disaster.go.th/index.php/s/bbmZcMzMaXMozdB
- แหล่งทดแทน:
  - [DOAE – สรุปข้อมูลประสบภัยด้านพืชรายปี (data.go.th)](https://data.go.th/en/dataset/disaster3) — ปี 2567 เท่านั้น
  - [ระบบช่วยเหลือเกษตรกรผู้ประสบภัย DOAE](https://disaster.doae.go.th/report/index) — ต้องล็อกอิน — ไม่ใช่ open data
- หมายเหตุ: ช่วงที่ขอ (2561) ไม่มีในชุด ปภ. ที่เปิดได้ (เริ่ม 2562). ต้องเปิดไฟล์ดูว่ามีคอลัมน์ 'พื้นที่การเกษตรเสียหาย (ไร่)' รายจังหวัดหรือไม่

### D07 ข้อมูลฝนเชิงพื้นที่รายจังหวัด (IDW)  [ได้บางส่วน]
- เจ้าของ: สถาบันสารสนเทศทรัพยากรน้ำ (สสน. HII)
- รูปแบบ/ขอบเขตที่ต้องการ: CSV | 77 จังหวัดรายเดือน (2561–2562)
- License: CC BY-NC
- Join key: ชื่อจังหวัด → pro_code, year, month
- สิ่งที่พบ: data.go.th ชุด 'ปริมาณฝนเชิงพื้นที่' ของ สสน. ตรงกับที่ต้องการ: ฝนเฉลี่ยรายเดือนรายจังหวัด คำนวณด้วย IDW จากสถานี TMD แต่ปีข้อมูลเริ่ม 2562 (ไม่มี 2561)
- แหล่งหลัก:
  - [ปริมาณฝนเชิงพื้นที่ (spatial-rain)](https://data.go.th/en/dataset/spatial-rain) — 2562–2568, CSV, อัปเดตรายเดือน; กดดาวน์โหลดผ่านเบราว์เซอร์
  - [อุณหภูมิสูงสุด/ต่ำสุดรายจังหวัดรายเดือน (tmax-tmin)](https://data.go.th/en/dataset/tmax-tmin) — ชุดคู่กันจาก สสน. 2562–2569
- แหล่งทดแทน:
  - [Open-Meteo Historical API (ERA5) – สำหรับปี 2561](https://archive-api.open-meteo.com/v1/archive?latitude=14.97&longitude=102.10&start_date=2018-01-01&end_date=2018-12-31&daily=precipitation_sum&timezone=Asia/Bangkok) — ใช้ centroid จังหวัดจาก GeoJSON, รวมรายวัน→รายเดือน; ระบุชัดว่าเป็น reanalysis ไม่ใช่ IDW
- หมายเหตุ: ถ้าใช้ Open-Meteo ต้องอ้างอิง Open-Meteo + ERA5 (Copernicus) และใช้แบบ non-commercial ฟรี. ค่าจาก reanalysis จะต่างจาก IDW ของ สสน. — อย่าผสมในกราฟเดียวโดยไม่ระบุ

### D08 สถิติฝนสะสมเฉลี่ยประเทศระยะยาว  [ใช้แหล่งทดแทน]
- เจ้าของ: สถาบันสารสนเทศทรัพยากรน้ำ (สสน. HII)
- รูปแบบ/ขอบเขตที่ต้องการ: CSV | ภาพรวมประเทศ (1970–2025)
- License: ตามแหล่งทดแทน
- Join key: year
- สิ่งที่พบ: ไม่พบชุด CSV ฝนรายปีระดับประเทศระยะยาวของ สสน. ที่ดาวน์โหลดได้. รายงานประจำปี thaiwater.net ให้ค่าเป็นรายปี (เช่น ปี 2566 ฝนเฉลี่ย 1,408 มม. ต่ำกว่าค่าปกติ 95 มม. หรือ ~6%) แต่ไม่มีไฟล์อนุกรมเวลา
- แหล่งหลัก:
  - [สถานการณ์น้ำประเทศไทย ปี 2566 (thaiwater.net)](https://thaiwater.net/uploads/contents/current/YearlyReport2023/summary.html) — ใช้ตรวจเทียบค่าแต่ละปี; ปีอื่นเปลี่ยน YearlyReport20XX
- แหล่งทดแทน:
  - [World Bank CCKP – Thailand historical climate (CRU, 1901–ปัจจุบัน)](https://climateknowledgeportal.worldbank.org/country/thailand/climate-data-historical) — ฝนรายปีระดับประเทศ ดาวน์โหลดผ่านหน้า Data Download
  - [Open-Meteo Historical API (ERA5, 1940–ปัจจุบัน)](https://open-meteo.com/en/docs/historical-weather-api) — เฉลี่ยหลายจุดทั่วประเทศ (เช่น centroid 77 จังหวัด) เพื่อสร้างอนุกรม 1970–2025
- หมายเหตุ: แนะนำ CRU (CCKP) เป็นหลักเพราะมาจากสถานีและใช้กันแพร่หลาย; ระบุใน dashboard ว่าเป็นแหล่งทดแทน ไม่ใช่ตัวเลข สสน.

### D09 ข้อมูลตรวจวัดอุตุนิยมวิทยาเพื่อการเกษตร  [ได้บางส่วน]
- เจ้าของ: กรมอุตุนิยมวิทยา (TMD)
- รูปแบบ/ขอบเขตที่ต้องการ: JSON API / Cache | 34 สถานีตรวจวัดทั่วประเทศ
- License: ต้องลงทะเบียนผู้ใช้ TMD
- Join key: station → พิกัด → จังหวัด (point-in-polygon กับ GeoJSON)
- สิ่งที่พบ: TMD API มีบริการ Station, WeatherToday v2 (07:00 + สถิติ 24 ชม.), Weather3Hours v2 (~122–125 สถานี), ThailandClimateNormal (1981–2010), WeatherForecast7Days รายจังหวัด. ไม่พบ endpoint เฉพาะ agromet 34 สถานีในรายการ API. เว็บบล็อกการดึงอัตโนมัติ และขอให้ลงทะเบียนเพื่อรับ uid/ukey
- แหล่งหลัก:
  - [TMD API – รายการบริการ](https://data.tmd.go.th/api/index1.php) — ลงทะเบียนเพื่อรับ uid/ukey; ใช้ Station + WeatherToday/V2
  - [คู่มือบริการข้อมูลผ่าน API (PDF)](https://www.tmd.go.th/media/docinfo/info_บรการขอมลอตนยมวทยาและแผนดนไหวผาน-api.pdf)
- แหล่งทดแทน:
  - [Open-Meteo Historical API](https://open-meteo.com/en/docs/historical-weather-api) — ใช้พิกัดสถานี TMD เพื่อดึงอุณหภูมิ ฝน ความชื้น ET0 ย้อนหลัง; ไม่ต้องใช้ key (non-commercial)
  - [อุณหภูมิสูงสุด/ต่ำสุดรายจังหวัด (สสน.)](https://data.go.th/en/dataset/tmax-tmin) — รายเดือนรายจังหวัด
- หมายเหตุ: ถ้าต้องเก็บเป็น cache: ดึง API แล้วบันทึกเป็น data/cache/tmd_YYYYMMDD.json เพื่อไม่ให้ dashboard เรียก API ตรง (CORS/โควตา)

### D10 ขอบเขตการปกครองรายจังหวัด  [ใช้ได้]
- เจ้าของ: กรมการปกครอง / GISTDA
- รูปแบบ/ขอบเขตที่ต้องการ: GeoJSON | 77 จังหวัด
- License: ไม่ระบุ license ใน README — ระบุที่มาเมื่อเผยแพร่
- Join key: pro_code (key หลักของทั้งโปรเจกต์)
- สิ่งที่พบ: OpenGISData-Thailand (GitHub) มี provinces.geojson 77 จังหวัด คุณสมบัติ pro_code, pro_th, pro_en, reg_nesdb, reg_royin, perimeter, area_sqkm
- แหล่งหลัก:
  - [provinces.geojson (raw)](https://raw.githubusercontent.com/chingchai/OpenGISData-Thailand/master/provinces.geojson) — มี member 'crs' แบบเก่า — ลบออกหรือ reproject ให้เป็น WGS84 ตาม RFC 7946
  - [Repo OpenGISData-Thailand](https://github.com/chingchai/OpenGISData-Thailand) — มีระดับอำเภอ/ตำบลด้วย
- แหล่งทดแทน:
  - [GeoThai data releases](https://github.com/GeoThai/data/releases) — ทางเลือกอื่น
  - [thailand-geography-json](https://github.com/thailand-geography-data/thailand-geography-json) — รายชื่อ/รหัสจังหวัด ใช้ทำตาราง lookup
- หมายเหตุ: ไฟล์ใหญ่ → simplify ด้วย mapshaper (เช่น 5–10%) ก่อนฝังลง dashboard

## ข้อตกลงร่วม
• ปี: แหล่งไทยส่วนใหญ่ใช้ พ.ศ. → ค.ศ. = พ.ศ. − 543 (2550–2562 = 2007–2019). ข้อมูลพืชบางชนิดเป็น "ปีเพาะปลูก" (เช่น 2562/63) ให้เก็บทั้ง crop_year_label และ year_ce (ปีเริ่ม)
• จังหวัด: ใช้ pro_code (รหัส 2 หลักตามกรมการปกครอง) เป็น key หลัก. ทำ mapping ชื่อไทย/อังกฤษ เพราะแต่ละแหล่งสะกดไม่เหมือนกัน (เช่น "กรุงเทพมหานคร" / "กรุงเทพฯ", "บึงกาฬ" ตั้งปี 2554 จึงไม่มีข้อมูลก่อนหน้า — ปี 2550–2553 จะมี 76 จังหวัด)
• หน่วย: เนื้อที่ = ไร่ (1 ไร่ = 0.16 เฮกตาร์), ผลผลิต = ตัน, ผลผลิตต่อไร่ = กก./ไร่, ราคา = บาท/กก., ต้นทุน = บาท/ไร่ หรือ บาท/กก., ฝน = มม.
• ไฟล์ CSV ภาษาไทยอาจเป็น UTF-8 (มี BOM) หรือ TIS-620/cp874 — ลองอ่านทั้งสองแบบ
• metadata ใน catalog หลายชุดระบุ "ปีล่าสุด" ไม่ตรงกับไฟล์จริง — เชื่อข้อมูลในไฟล์ ไม่ใช่ metadata
• เก็บ source_id และ source_url ทุกแถว เพื่อให้ dashboard แสดงที่มาได้

สคีมา:
```
province_code,province_th,year_ce,period,crop,metric,value,unit,source_id,source_url
30,นครราชสีมา,2019,annual,cassava,production,7012345,ton,D01,https://catalog.oae.go.th/dataset/dataoae1304
30,นครราชสีมา,2019,2019-W14,cassava,farmgate_price,1.95,THB/kg,D02,...
```

## ข้อจำกัด
• data.go.th: หน้า dataset ส่วนใหญ่แสดงลิงก์ดาวน์โหลดเป็น template ที่ยังไม่ render (${cur_meta...}) เมื่อดึงอัตโนมัติ และ API package_search ใช้ได้ไม่สม่ำเสมอ → เปิดผ่านเบราว์เซอร์แล้วกดดาวน์โหลดเอง
• ชุดข้อมูลบน data.go.th จำนวนมากเป็นของ "สำนักงานจังหวัด" รายจังหวัด ไม่ใช่ระดับประเทศ — อย่านำมาต่อกันโดยไม่ตรวจความสอดคล้อง
• catalog.oae.go.th บล็อกการดึงหน้าที่ 2+ ของหมวดและ API ด้วย robots.txt → ต้องเปิดด้วยเบราว์เซอร์เพื่อดูรายการครบ (หมวดผลผลิตมี 70 ชุด, ราคา 35 ชุด)
• data.tmd.go.th บล็อกการดึงอัตโนมัติ และต้องลงทะเบียนเพื่อรับ uid/ukey
• ระบบ disaster.doae.go.th ต้องล็อกอินด้วย ThaiD จึงไม่ใช่ open data โดยตรง
