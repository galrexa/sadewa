# SADEWA - Smart Assistant for Drug & Evidence Warning

![SADEWA Logo](https://img.shields.io/badge/SADEWA-AI%20Medical%20System-green?style=for-the-badge)
![Meta Llama](https://img.shields.io/badge/Meta%20Llama-3.3--70B-blue?style=for-the-badge)
![FastAPI](https://img.shields.io/badge/FastAPI-2.1.0-009688?style=for-the-badge)
![React](https://img.shields.io/badge/React-18.0-61DAFB?style=for-the-badge)

> **AI-powered Medical Information System** menggunakan Meta Llama untuk analisis interaksi obat dan dukungan keputusan klinis di lingkungan kesehatan Indonesia.

## 📋 Deskripsi Aplikasi

**SADEWA** adalah sistem informasi medis berbasis AI yang dirancang khusus untuk **membantu tenaga medis** dalam:

### 🎯 **Fungsi Utama:**

- **Patient Management** - Registrasi dan manajemen data pasien dengan validasi medis
- **AI Diagnosis Support** - Saran diagnostik menggunakan Llama-3.3-70b dengan confidence scoring
- **Drug Interaction Analysis** - Deteksi real-time interaksi obat dengan tingkat keparahan
- **Medical Records (Anamnesis)** - Pencatatan gejala terstruktur untuk AI analysis
- **Clinical Decision Support** - Sistem pendukung keputusan klinis terintegrasi

### **🏥 Medical Data Foundation**

- **ICD-10 Classification** - Complete WHO diagnostic codes dengan terminologi Indonesia
- **FORNAS Drug Database** - Formularium Nasional Indonesia untuk medication reference
- **Professional Drug Interactions** - Validated data dari MIMS.com dan Drugs.com
- **Clinical Decision Rules** - Evidence-based medical logic untuk AI reasoning

### 🏥 **Target Pengguna:**

- Dokter dan tenaga medis
- Farmasis klinis
- Rumah sakit dan klinik di Indonesia
- Sistem informasi kesehatan terintegrasi

---

## 🤖 Arsitektur AI Implementation

### **Meta Llama Integration**

```
Groq API → Llama-3.3-70B-Versatile → Clinical Decision Support
```

#### **1. AI Service Architecture**

```python
# Enhanced Groq Service dengan Multi-layered Clinical Decision Support
class GroqService:
    def __init__(self):
        self.model = "llama-3.3-70b-versatile"
        self.temperature = 0.1  # Low temperature untuk konsistensi medical advice
        self.max_tokens = 2000
```

#### **2. Clinical Prompt Engineering**

- **Specialized Medical Prompts** - Context-aware untuk setting healthcare Indonesia
- **Patient-Specific Analysis** - Mengintegrasikan data pasien, alergi, riwayat medis
- **Evidence-Based Reasoning** - Structured clinical reasoning dengan confidence scoring

#### **3. AI Analysis Types**

```python
class AIAnalysisType(str, Enum):
    DIAGNOSIS = "diagnosis"              # Saran diagnostik berdasarkan gejala
    DRUG_INTERACTION = "drug_interaction" # Analisis interaksi obat
    RISK_ASSESSMENT = "risk_assessment"   # Penilaian risiko klinis
    TREATMENT_RECOMMENDATION = "treatment_recommendation" # Saran pengobatan
```

#### **4. Performance Optimization**

- **Intelligent Caching** - Cache drug interaction results dengan hash-based lookup
- **Background Processing** - Async AI analysis untuk response time optimal
- **Severity-Based Prioritization** - Major interactions diproses dengan prioritas tinggi

### **Data Flow Architecture**

```
┌─────────────────┐    ┌─────────────────┐    ┌──────────────────┐
│   Patient Data  │───▶│ AI Prompt Gen.  │───▶│ Llama 3.3-70B    │
│  • Demographics │    │ • Clinical      │    │ via Groq API     │
│  • Symptoms     │    │   Context       │    │                  │
│  • Medications  │    │ • Medical       │    │                  │
│  • Allergies    │    │   History       │    │                  │
└─────────────────┘    └─────────────────┘    └──────────────────┘
                                                         │
┌─────────────────┐    ┌─────────────────┐              │
│ FORNAS Database │    │ Drug Interaction│              │
│ • Drug Names    │───▶│ Lookup Engine   │─────────────▶│
│ • Dosages       │    │ • MIMS Data     │              │
│ • Categories    │    │ • Drugs.com     │              │
└─────────────────┘    └─────────────────┘              │
                                                         ▼
┌─────────────────┐    ┌─────────────────┐    ┌──────────────────┐
│  Audit Logging  │◀───│  Cache Storage  │◀───│ Clinical Parser  │
│ • AI Requests   │    │ • Hash-based    │    │ • JSON Response  │
│ • Confidence    │    │ • TTL Cache     │    │ • Confidence     │
│ • Model Version │    │ • Performance   │    │ • Recommendations│
└─────────────────┘    └─────────────────┘    └──────────────────┘
                                                         │
                                                         ▼
                                              ┌──────────────────┐
                                              │Medical Decision  │
                                              │Support System    │
                                              │ • Risk Level     │
                                              │ • Contraindic.   │
                                              │ • Monitoring     │
                                              └──────────────────┘
```

#### **Flow Description:**

1. **Input Processing** - Patient data + symptoms → Clinical context generation
2. **AI Analysis** - Structured prompt → Llama 3.3-70B → Clinical reasoning
3. **Data Enhancement** - FORNAS database + Drug interactions → Comprehensive analysis
4. **Response Processing** - AI output → Parsed recommendations + confidence scoring
5. **Performance Layer** - Caching + audit logging → Optimized repeated queries

## 📊 Medical Database Integration

### **Comprehensive Medical Reference Data**

#### **1. ICD-10 Diagnosis Database**

- **Complete ICD-10 Classification** - Full International Classification of Diseases
- **Bilingual Support** - English dan Indonesian terminology
- **Category Indexing** - Organized by medical specialties (A00-B99, C00-D48, etc.)
- **Search Optimization** - Fast lookup dengan prefix matching

#### **2. FORNAS Drug Database**

- **Indonesian National Formulary** - Complete drug database from FORNAS
- **Generic & Brand Names** - Comprehensive medication naming
- **Dosage Information** - Standard dosing guidelines
- **Category Classification** - Organized by therapeutic categories

#### **3. Drug Interaction Dataset**

- **Professional Sources** - Data sourced from **MIMS.com** and **Drugs.com**
- **Severity Classification** - Major, Moderate, Minor interactions
- **Clinical Evidence** - Mechanism of action dan clinical effects
- **Indonesia-Specific** - Focused on medications available in Indonesia

### **Data Quality & Sources**

```
📋 ICD-10: WHO International Classification (Indonesian adaptation)
💊 FORNAS: Formularium Nasional Indonesia (Official)
⚠️ Drug Interactions: MIMS Medical + Drugs.com Clinical Database
🔍 Total Records: 10,000+ drugs, 50,000+ interactions, 14,000+ ICD codes
```

### **Prerequisites**

- Python 3.9+
- Node.js 18+
- MySQL 8.0+
- Groq API Key

### **Backend Setup**

```bash
# Clone repository
git clone <repository-url>
cd sadewa-backend

# Install dependencies
pip install -r requirements.txt

# Environment configuration
cp .env.example .env
# Edit .env dengan konfigurasi database dan API keys
```

### **Environment Variables**

```bash
# Database Configuration
DATABASE_URL=mysql+pymysql://user:password@localhost/sadewa_db
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=yourpassword
DB_NAME=sadewa_db

# AI Service
GROQ_API_KEY=your_groq_api_key_here

# Application
ENVIRONMENT=development
PORT=8000
```

### **Frontend Setup**

```bash
cd sadewa-frontend

# Install dependencies
npm install

# Environment configuration
echo "VITE_API_BASE_URL=http://localhost:8000" > .env

# Start development server
npm run dev
```

### **Database Setup**

```bash
# Import database schema
mysql -u root -p sadewa_db < sadewa_db.sql

# Run application
cd sadewa-backend
python main.py
```

---

## 🏗️ Technical Architecture

### **Backend Stack**

- **FastAPI** - High-performance async web framework
- **SQLAlchemy 2.0** - Modern ORM dengan async support
- **MySQL** - Primary database dengan indexing optimization
- **Pydantic** - Data validation dan serialization
- **Groq SDK** - Meta Llama API integration

### **Frontend Stack**

- **React 18** - Modern UI framework dengan hooks
- **Vite** - Fast build tool dan dev server
- **Tailwind CSS** - Utility-first CSS framework
- **Lucide Icons** - Consistent medical iconography
- **Axios** - HTTP client dengan interceptors

### **Database Schema**

```sql
-- Core Tables
patients (id, no_rm, name, age, gender, medical_data)
medical_records (id, no_rm, symptoms, ai_suggestions, confidence)

-- Medical Reference Data
icds (code, name_en, name_id, category)           -- ICD-10 diagnosis codes
drugs (id, name, generic_name, fornas_category)   -- FORNAS drug database
drug_interactions (drug_a, drug_b, severity, clinical_effect) -- MIMS & Drugs.com data

-- AI & Performance
ai_analysis_logs (analysis_type, confidence_score, model_version)
drug_interaction_cache (drug_combination_hash, results)
```

---

## 🔄 API Endpoints

### **Patient Management**

```http
GET    /api/patients              # List all patients
POST   /api/patients              # Create new patient
GET    /api/patients/{id}         # Get patient detail
PUT    /api/patients/{id}         # Update patient
DELETE /api/patients/{id}         # Delete patient
```

### **AI Analysis**

```http
POST   /api/ai/analyze/drug-interactions    # Drug interaction analysis
POST   /api/ai/analyze/diagnosis            # AI diagnosis suggestions
GET    /api/ai/test-connection              # Test Groq API connection
```

### **Drug Services**

```http
GET    /api/drugs/search                    # Search drug database
GET    /api/drugs/autocomplete             # Drug name autocomplete
POST   /api/drugs/check-interactions       # Check specific interactions
```

---

## 🚧 Batasan & Pengembangan Lanjutan

### **⚠️ Current Limitations**

#### **1. AI Model Limitations**

- **Model Scope** - Terbatas pada Llama-3.3-70B, belum fine-tuned untuk medical Indonesia
- **Language Support** - Primarily English medical terminology, Indonesian translation manual
- **Real-time Learning** - Belum ada continuous learning dari clinical feedback
- **Offline Capability** - Membutuhkan internet connection untuk AI analysis

#### **2. Clinical Features Missing**

- **Electronic Health Records (EHR) Integration** - Belum terintegrasi dengan system HIS/EMR
- **Laboratory Results Analysis** - Belum support hasil lab untuk diagnosis
- **Medical Imaging Support** - Tidak ada analisis X-ray, CT scan, MRI
- **Prescription Writing** - Belum ada modul penulisan resep elektronik
- **Clinical Guidelines Database** - Belum terintegrasi dengan guideline medis Indonesia

#### **3. Security & Compliance**

- **HIPAA/Medical Data Compliance** - Belum implement full medical data encryption
- **Audit Trail** - Basic logging, belum comprehensive audit system
- **User Role Management** - Belum ada role-based access control (doctor/nurse/pharmacist)
- **Data Backup & Recovery** - Belum implement automated backup system

#### **4. Performance & Scalability**

- **Concurrent Users** - Belum tested untuk high-load scenarios
- **Database Optimization** - Index optimization belum optimal untuk large datasets
- **AI Response Time** - Masih bergantung pada Groq API latency
- **Mobile Optimization** - Frontend belum fully mobile-responsive

## 📝 License & Credits

### **Development Team**

- **AI Integration** - Meta Llama 3.3-70B via Groq API
- **Backend Development** - FastAPI with SQLAlchemy
- **Frontend Development** - React with modern tooling
- **Medical Consultation** - Healthcare domain expertise

### **Acknowledgments**

- **Meta Llama** for providing advanced language model
- **Groq** for high-performance AI inference API
- **MIMS & Drugs.com** for comprehensive drug interaction data
- **FORNAS Indonesia** for national drug formulary database
- **WHO ICD-10** for international diagnostic classification
- **Indonesian Healthcare Community** for domain knowledge validation

---

### **Technical Support**

- **Documentation**: Available in `/docs` endpoint
- **API Testing**: Interactive docs at `/docs` and `/redoc`

---
