# Business Requirements Document (BRD)
## Project Name: Thailand Agricultural Production & Economics Analytics Dashboard
**Target Platform:** Web-Based Interactive Dashboard (Python + Plotly)  
**Recipient:** Developer / Engineering Team (Antigravity)  
**Version:** 2.0  
**Status:** Draft / Approved for Development  

---

## 1. Executive Summary & Objectives (วัตถุประสงค์และเป้าหมายของระบบ)

โครงการนี้มีวัตถุประสงค์เพื่อพัฒนา Dashboard เชิงโต้ตอบ (Interactive Dashboard) สำหรับวิเคราะห์โครงสร้างการผลิต พืชเศรษฐกิจ สภาพอากาศ ปัจจัยขับเคลื่อนผลผลิต และเศรษฐศาสตร์ฟาร์มของประเทศไทย ครอบคลุม 77 จังหวัดทั่วประเทศ และ 26 ชนิดสินค้าเกษตร ในช่วงปี พ.ศ. 2550–2562

### 1.1 Core Objectives
1. **เข้าใจโครงสร้างการผลิตสินค้าเกษตรไทย:** สำรวจเนื้อที่เพาะปลูก เนื้อที่เก็บเกี่ยว และผลผลิต ครอบคลุม 26 สินค้าเกษตร พร้อมทางลัดเลือกพืชเศรษฐกิจหลัก 4 ชนิด (ข้าวนาปี, ข้าวนาปรัง, มันสำปะหลัง, ข้าวโพดเลี้ยงสัตว์)
2. **แดชบอร์ด 4 แท็บวิเคราะห์เชิงลึก:** แบ่งออกเป็น 4 แท็บหลักที่ตอบสนองต่อ Global Filters ร่วมกันอย่างเป็นเอกภาพ
3. **Global Filter Bar ด้านบน:** มีระบบกรองข้อมูลส่วนกลางเพื่อควบคุมการแสดงผลทุกแท็บร่วมกัน
4. **แสดงผลด้วย Map และ Chart เชิงเปรียบเทียบ:** ใช้ Choropleth Map แสดงข้อมูลระดับ 77 จังหวัด คู่ขนานกับกราฟเปรียบเทียบแนวโน้มรายปี
5. **วิเคราะห์อิทธิพลของสภาพอากาศ:** เชื่อมโยงข้อมูลฝนเชิงพื้นที่ (HII IDW), ฝนสะสมช่วงฤดูเพาะปลูก (พ.ค.–ต.ค.), อุณหภูมิ และสถานีตรวจวัด TMD
6. **วิเคราะห์ปัจจัยขับเคลื่อนผลผลิต (Production Drivers):** ประเมินระบบชลประทาน (RID), ความเหมาะสมของดิน (Agri-Map LDD), ภัยแล้ง/อุทกภัย (DOAE/DDPM) และเทคโนโลยีเครื่องจักรกล
7. **วิเคราะห์เศรษฐศาสตร์ฟาร์ม & เครื่องคำนวณกำไร:** วิเคราะห์ราคาหน้าฟาร์มจริง (สศก.), ต้นทุนการผลิต และ Profit & Break-even Calculator ที่แยกข้อมูลเกษตรกรจริงออกจากเกณฑ์ภาครัฐ

---

## 2. Technical Stack & Architectural Guidelines (ข้อกำหนดทางเทคนิค)

* **Backend Framework:** Python (เช่น Dash, Streamlit หรือ FastAPI + Plotly Component Framework)
* **Visualization Library:** Plotly (Plotly Express / Graph Objects) เป็นหลัก
* **Interactivity & State Management:** 
  * ทุกกราฟและองค์ประกอบในทุก แท็บ ต้องเชื่อมโยง (Cross-filtering / Dynamic Callbacks) กับ Global Filter
  * การเปลี่ยนตัวกรองใน Global Filter จะต้อง Update ข้อมูลในทุกแท็บพร้อมกันโดยอัตโนมัติ
* **Data Sources Baseline:** ข้อมูลเตรียมพร้อมในรูปแบบ Dataframe / Database ช่วงปี พ.ศ. 2550 – 2562

---

## 3. Global Filter Bar (ระบบตัวกรองส่วนกลางด้านบน)

Global Filter Bar ต้องประดิษฐานอยู่ส่วนบนสุดของ Dashboard หน้าจอเสมอ (Sticky / Header Area) ประกอบด้วย:

1. **ภูมิภาค (Region Filter):** Dropdown เลือกรวมทั้งประเทศ หรือแยกรายภาค (เหนือ, ตะวันออกเฉียงเหนือ, กลาง, ใต้, ตะวันออก, ตะวันตก)
2. **จังหวัด (Province Filter):** Dropdown แบบ Dynamic Filter (รายการจังหวัดจะเปลี่ยนตามภูมิภาคที่เลือก)
3. **ชนิดพืช (Crop Filter):** Dropdown เลือกได้ 26 ชนิดพืช พร้อม **Quick-Select Shortcuts Buttons** 4 พืชหลัก:
   * [ข้าวนาปี] [ข้าวนาปรัง] [มันสำปะหลัง] [ข้าวโพดเลี้ยงสัตว์]
4. **ปี พ.ศ. (Year / Range Filter):** Slider หรือ Dropdown ช่วงปี พ.ศ. 2550 – 2562
5. **ตัวชี้วัดหลัก (Key Metric Selector):**
   * เนื้อที่เพาะปลูก (ไร่)
   * เนื้อที่เก็บเกี่ยว (ไร่)
   * ผลผลิตรวม (ตัน)
   * ผลผลิตต่อไร่ (กก./ไร่)
6. **ปุ่มควบคุมและสถานะ:**
   * **Button:** `Reset Filters` (คืนค่าตัวกรองทั้งหมดเป็น Default)
   * **Active Filter Badges:** แถบแสดงสถานะตัวกรองปัจจุบันที่ User เลือก (เช่น `ภาคเหนือ` | `เชียงใหม่` | `ข้าวนาปี` | `ปี 2562`)

---

## 4. Tab Structure & Functional Requirements (รายละเอียดทั้ง 4 แท็บ)

### **Tab 1: โครงสร้างการผลิตและการกระจายตัวเชิงพื้นที่ (Production Structure & Spatial Distribution)**
* **วัตถุประสงค์:** แสดงภาพรวมการผลิต การกระจายตัวเชิงพื้นที่ 77 จังหวัด และแนวโน้มประวัติศาสตร์
* **องค์ประกอบ visual:**
  1. **Thailand Choropleth Map (77 จังหวัด):** แสดงความเข้มของสีตาม Metric ที่เลือกใน Global Filter (เช่น ผลผลิตรวม หรือ ผลผลิตต่อไร่) มี Hover Tooltip บอกรายละเอียดจังหวัด
  2. **Historical Trend Chart (Line / Bar Chart):** แสดงแนวโน้มการเปลี่ยนแปลงตามช่วงปี (2550-2562) เปรียบเทียบตามตัวกรองที่เลือก
  3. **Top / Bottom Ranking Bar Chart:** แสดง 10 อันดับจังหวัดที่มีผลผลิต/พื้นที่สูงสุด และต่ำสุด
  4. **Summary KPI Cards:** แสดงค่ารวม (Total Yield, Total Area) และค่าเฉลี่ย (Avg Yield per Rai) ตามตัวกรองปัจจุบัน

---

### **Tab 2: สภาพอากาศและสถานการณ์เพาะปลูก (Weather & Climate Impact Analysis)**
* **วัตถุประสงค์:** วิเคราะห์ความสัมพันธ์ระหว่างปัจจัยภูมิอากาศกับปริมาณผลผลิตเกษตร
* **องค์ประกอบ visual:**
  1. **Spatial Rainfall Map / Heatmap (HII IDW):** แสดงการกระจายตัวของปริมาณน้ำฝนเชิงพื้นที่ 77 จังหวัด
  2. **Growing Season Cumulative Rainfall Chart (พ.ค.–ต.ค.):** กราฟแท่ง/เส้น แสดงปริมาณฝนสะสมในช่วงฤดูเพาะปลูกเทียบกับค่าเฉลี่ยปกติ
  3. **Temperature & TMD Station Correlation:** กราฟวิเคราะห์อุณหภูมิ (สูงสุด/เฉลี่ย) จากสถานีตรวจวัดอากาศกรมอุตุนิยมวิทยา (TMD)
  4. **Climate vs. Yield Scatter / Dual-Axis Chart:** กราฟความสัมพันธ์แบบ Scatter Plot หรือ Dual-Axis แสดงจุดตัดระหว่างปริมาณฝน/อุณหภูมิ กับผลผลิตต่อไร่ (Yield per Rai) เพื่อดู Correlation

---

### **Tab 3: ปัจจัยขับเคลื่อนผลผลิตและข้อจำกัดเชิงพื้นที่ (Production Drivers & Spatial Constraints)**
* **วัตถุประสงค์:** วิเคราะห์โครงสร้างพื้นฐาน ภัยธรรมชาติ ข้อจำกัดดิน และเทคโนโลยี
* **องค์ประกอบ visual:**
  1. **Irrigation Coverage Analysis (RID):** กราฟเปรียบเทียบพื้นที่ในเขตชลประทาน vs นอกเขตชลประทาน กับระดับผลผลิตที่ได้รับ
  2. **Agri-Map Soil Suitability Breakdown (LDD):** Pie Chart / Stacked Bar แสดงสัดส่วนการปลูกพืชในพื้นที่ความเหมาะสมของดิน 4 ระดับ (เหมาะสมมาก-S1, ปานกลาง-S2, น้อย-S3, ไม่เหมาะสม-N)
  3. **Disaster Impact Tracker (DOAE / DDPM):** กราฟแสดงสถิติพื้นที่ประสบภัยแล้ง และภัยอุทกภัย (น้ำท่วม) ที่ส่งผลกระทบต่อพื้นที่เสียหายจริง
  4. **Mechanization & Technology Index:** ตัวชี้วัด/กราฟแสดงระดับการใช้เครื่องจักรกลการเกษตรในพื้นที่

---

### **Tab 4: เศรษฐศาสตร์ฟาร์มและเครื่องคำนวณกำไรสุทธิ (Farm Economics & Profitability Calculator)**
* **วัตถุประสงค์:** วิเคราะห์ราคา ต้นทุน และสร้างเครื่องมือคำนวณผลตอบแทนทางการเกษตร
* **องค์ประกอบ visual:**
  1. **Historical Farmgate Price Trend (สศก.):** กราฟเส้นแสดงราคาที่เกษตรกรขายได้จริง ณ หน้าฟาร์ม (Farmgate Price) ย้อนหลัง
  2. **Cost Structure Breakdown:** Donut Chart / Stacked Bar แยกโครงสร้างต้นทุน (ค่าผันแปร: เมล็ดพันธุ์ ปุ๋ย แรงงาน, ค่าคงที่: ค่าเช่า land)
  3. **Interactive Profit & Break-even Calculator (เครื่องคำนวณกำไรและจุดคุ้มทุน):**
     * **Input Panel (User Adjustment):** ให้ผู้ใช้ปรับเปลี่ยนค่าได้ เช่น
       * *ราคาขายจริงของเกษตรกร (บาท/กิโลกรัม)*
       * *ต้นทุนจริงของเกษตรกร (บาท/ไร่)*
       * *ผลผลิตที่ได้จริง (กก./ไร่)*
     * **Comparison Output (Farmer Reality vs. Government Standard):**
       * แสดงผลเปรียบเทียบ 2 มุมมองชัดเจน: **[ข้อมูลเกษตรกรจริง (User/Field Reality)]** vs **[เกณฑ์มาตรฐานภาครัฐ/สศก. (Benchmark)]**
       * คำนวณอัตโนมัติ: **กำไรสุทธิ (Net Profit/Rai)**, **จุดคุ้มทุน (Break-Even Price/Yield)**, และ **อัตราผลตอบแทน (ROI %)**

---

## 5. Non-Functional Requirements & Design Principles

1. **Responsiveness & Performance:**
   * การ Render กราฟทุกตัวใน Plotly ต้องตอบสนองรวดเร็ว (Filter Update Response Time < 2 วินาที)
   * รองรับการแสดงผลผ่าน Web Browsers (Chrome, Firefox, Edge, Safari)
2. **UI/UX Design Concept:**
   * **Color Palette:** ใช้โทนสีการเกษตรที่ดูทันสมัย (เช่น Modern Green, Earth Tone, Teal Accent)
   * **Consistency:** ใช้ Metric Units สม่ำเสมอ (ไร่, ตัน, กก./ไร่, บาท)
   * **Data Handling:** มีการจัดการ Missing Value หรือ Data Null ในบางจังหวัด/บางปี อย่างเหมาะสม (แสดง 'N/A' หรือ Gray Overlay บน Map)

---

## 6. Project Deliverables

1. **Python Source Code Directory Structure:**
   * Backend Core (Data processing & Callbacks)
   * Dashboard Components (Layout, Global Filter Bar, Tabs 1-4)
   * Assets (CSS Styling, Custom Theme)
2. **Data Pipeline & Models:** Scripts สำหรับ Load/Clean/Transform ข้อมูลทั้ง 77 จังหวัด, 26 พืช, และข้อมูลสภาพอากาศ/เศรษฐกิจ
3. **Deployment Package:** Dockerfile หรือ `requirements.txt` สำหรับนำไป Deployment

---