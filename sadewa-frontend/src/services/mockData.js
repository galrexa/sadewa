// src/services/mockData.js
// Mock data untuk fallback ketika backend tidak tersedia

export const mockPatients = [
  {
    id: "P001",
    name: "Bapak Agus Santoso",
    age: 72,
    gender: "Male",
    weight_kg: 68.5,
    height_cm: 165,
    medical_record_number: "MR001-2024",
    registration_date: "2024-01-15",
    diagnoses_icd10: ["I48.0", "I25.9", "M79.3"],
    diagnoses_text: [
      "Atrial Fibrillation (chronic)",
      "Chronic Ischemic Heart Disease",
      "Chronic knee pain (osteoarthritis suspected)",
    ],
    current_medications: [
      "Warfarin 5mg OD (for AF stroke prevention)",
      "Lisinopril 10mg OD (for hypertension)",
      "Metformin 500mg BID (for diabetes control)",
      "Atorvastatin 20mg ON (for dyslipidemia)",
    ],
    allergies: ["Penicillin (rash)", "Sulfonamides (mild GI upset)"],
    vital_signs: {
      blood_pressure: "138/82 mmHg",
      heart_rate: "78 bpm (irregular)",
      temperature: "36.7°C",
      respiratory_rate: "18/min",
      oxygen_saturation: "97% on room air",
    },
    laboratory_results: {
      last_updated: "2024-09-01",
      inr: 2.3,
      pt: 28.5,
      hemoglobin: 12.8,
      creatinine: 1.1,
      egfr: 68,
      hba1c: 7.2,
      ldl_cholesterol: 95,
    },
    clinical_notes: [
      {
        date: "2024-09-05",
        note: "Patient stable on current medications. INR in target range 2-3.",
      },
      {
        date: "2024-09-08",
        note: "Complains of worsening knee pain, requests pain medication. Currently using topical diclofenac with minimal relief.",
      },
    ],
    risk_factors: [
      "Age >65 years",
      "Male gender",
      "History of atrial fibrillation",
      "Diabetes mellitus",
      "Hypertension",
      "Chronic kidney disease stage 3a",
    ],
    contraindications: [
      "NSAIDs (due to warfarin + bleeding risk + CKD)",
      "Penicillin-based antibiotics",
      "High-dose aspirin",
    ],
  },
  {
    id: "P002",
    name: "Ibu Sari Dewi",
    age: 58,
    gender: "Female",
    weight_kg: 62.0,
    diagnoses: ["E11", "N18.3"],
    diagnoses_text: [
      "Type 2 diabetes mellitus",
      "Chronic kidney disease, stage 3",
    ],
    current_medications: ["Metformin 850mg", "Gliclazide 80mg"],
    allergies: [],
    notes: "DM type 2 dengan komplikasi nefropati diabetik",
  },
  {
    id: "P003",
    name: "Bapak Hendrik Wijaya",
    age: 65,
    gender: "Male",
    weight_kg: 78.0,
    diagnoses: ["I50.9", "J44.0", "E78.5"],
    diagnoses_text: [
      "Heart failure",
      "COPD with acute exacerbation",
      "Hyperlipidemia",
    ],
    current_medications: [
      "Digoxin 0.25mg",
      "Salbutamol inhaler",
      "Atorvastatin 20mg",
    ],
    allergies: ["Aspirin"],
    notes: "CHF NYHA class II, COPD eksaserbasi akut dalam remisi",
  },
  {
    id: "P004",
    name: "Ibu Maria Gonzalez",
    age: 45,
    gender: "Female",
    weight_kg: 55.0,
    diagnoses: ["I10", "G43.9"],
    diagnoses_text: ["Hypertension", "Migraine"],
    current_medications: ["Amlodipine 5mg", "Hydrochlorothiazide 25mg"],
    allergies: [],
    notes: "Hipertensi primer terkontrol, migraine episodik",
  },
  {
    id: "P005",
    name: "Bapak Rizky Rahman",
    age: 38,
    gender: "Male",
    weight_kg: 70.0,
    diagnoses: [],
    diagnoses_text: ["Healthy adult"],
    current_medications: [],
    allergies: [],
    notes: "Pemeriksaan rutin, tidak ada keluhan",
  },
  {
    id: "P006",
    name: "Ibu Fatimah Zahra",
    age: 67,
    gender: "Female",
    weight_kg: 58.0,
    diagnoses: ["M79.1", "K21.9"],
    diagnoses_text: ["Osteoarthritis", "GERD"],
    current_medications: ["Omeprazole 20mg", "Glucosamine 500mg"],
    allergies: ["Codeine"],
    notes: "Osteoartritis lutut bilateral, GERD terkontrol",
  },
  {
    id: "P007",
    name: "Bapak Ahmad Syarif",
    age: 52,
    gender: "Male",
    weight_kg: 75.0,
    diagnoses: ["E11", "I10", "E78.5"],
    diagnoses_text: ["Type 2 diabetes", "Hypertension", "Dyslipidemia"],
    current_medications: [
      "Metformin 1000mg",
      "Captopril 25mg",
      "Simvastatin 20mg",
    ],
    allergies: [],
    notes: "Sindrom metabolik, kontrol gula darah suboptimal",
  },
  {
    id: "P008",
    name: "Ibu Linda Sari",
    age: 29,
    gender: "Female",
    weight_kg: 52.0,
    diagnoses: ["O80", "Z34.9"],
    diagnoses_text: ["Post partum care", "Pregnancy supervision"],
    current_medications: ["Folic acid 5mg", "Iron supplement"],
    allergies: ["Sulfa drugs"],
    notes: "Post partum hari ke-10, menyusui eksklusif",
  },
  {
    id: "P009",
    name: "Bapak Sutrisno",
    age: 73,
    gender: "Male",
    weight_kg: 64.0,
    diagnoses: ["N40", "I10"],
    diagnoses_text: ["Benign prostatic hyperplasia", "Hypertension"],
    current_medications: ["Tamsulosin 0.4mg", "Amlodipine 10mg"],
    allergies: [],
    notes: "BPH dengan gejala LUTS sedang, hipertensi terkontrol",
  },
  {
    id: "P010",
    name: "Ibu Dewi Kusuma",
    age: 41,
    gender: "Female",
    weight_kg: 59.0,
    diagnoses: ["F32.9", "G47.9"],
    diagnoses_text: ["Depression", "Sleep disorder"],
    current_medications: ["Sertraline 50mg", "Lorazepam 0.5mg PRN"],
    allergies: ["Latex"],
    notes: "Depresi mayor episode tunggal, gangguan tidur sekunder",
  },
];

export const mockICD10 = [
  {
    code: "E11",
    name_id: "Diabetes mellitus tipe 2",
    name_en: "Type 2 diabetes mellitus",
  },
  {
    code: "E10",
    name_id: "Diabetes mellitus tipe 1",
    name_en: "Type 1 diabetes mellitus",
  },
  {
    code: "I10",
    name_id: "Hipertensi esensial",
    name_en: "Essential hypertension",
  },
  { code: "I48", name_id: "Fibrilasi atrial", name_en: "Atrial fibrillation" },
  {
    code: "I48.0",
    name_id: "Fibrilasi atrial paroksismal",
    name_en: "Paroxysmal atrial fibrillation",
  },
  {
    code: "I25.9",
    name_id: "Penyakit jantung iskemik kronik",
    name_en: "Chronic ischemic heart disease",
  },
  { code: "I50", name_id: "Gagal jantung", name_en: "Heart failure" },
  {
    code: "I50.9",
    name_id: "Gagal jantung tidak spesifik",
    name_en: "Heart failure, unspecified",
  },
  {
    code: "N18",
    name_id: "Penyakit ginjal kronik",
    name_en: "Chronic kidney disease",
  },
  {
    code: "N18.3",
    name_id: "Penyakit ginjal kronik stadium 3",
    name_en: "Chronic kidney disease, stage 3",
  },
  {
    code: "J44.0",
    name_id: "PPOK dengan eksaserbasi akut",
    name_en: "COPD with acute exacerbation",
  },
  {
    code: "E78.5",
    name_id: "Hiperlipidemia tidak spesifik",
    name_en: "Hyperlipidaemia, unspecified",
  },
  {
    code: "G43.9",
    name_id: "Migrain tidak spesifik",
    name_en: "Migraine, unspecified",
  },
  { code: "M79.1", name_id: "Mialgia", name_en: "Myalgia" },
  {
    code: "M79.3",
    name_id: "Pannikulitis tidak spesifik",
    name_en: "Panniculitis, unspecified",
  },
  {
    code: "K21.9",
    name_id: "Penyakit refluks gastroesofageal",
    name_en: "Gastro-oesophageal reflux disease",
  },
  {
    code: "N40",
    name_id: "Hiperplasia prostat jinak",
    name_en: "Benign prostatic hyperplasia",
  },
  {
    code: "F32.9",
    name_id: "Episode depresi mayor tidak spesifik",
    name_en: "Major depressive episode, unspecified",
  },
  {
    code: "G47.9",
    name_id: "Gangguan tidur tidak spesifik",
    name_en: "Sleep disorder, unspecified",
  },
  {
    code: "O80",
    name_id: "Persalinan tunggal spontan",
    name_en: "Single spontaneous delivery",
  },
  {
    code: "Z34.9",
    name_id: "Pengawasan kehamilan normal",
    name_en: "Supervision of normal pregnancy",
  },
];

export const mockDrugs = [
  {
    id: 1,
    nama_obat: "Parasetamol",
    nama_obat_internasional: "Paracetamol",
    display_name: "Parasetamol (Paracetamol)",
  },
  {
    id: 2,
    nama_obat: "Ibuprofen",
    nama_obat_internasional: "Ibuprofen",
    display_name: "Ibuprofen (Ibuprofen)",
  },
  {
    id: 3,
    nama_obat: "Warfarin",
    nama_obat_internasional: "Warfarin",
    display_name: "Warfarin (Warfarin)",
  },
  {
    id: 4,
    nama_obat: "Metformin",
    nama_obat_internasional: "Metformin",
    display_name: "Metformin (Metformin)",
  },
  {
    id: 5,
    nama_obat: "Lisinopril",
    nama_obat_internasional: "Lisinopril",
    display_name: "Lisinopril (Lisinopril)",
  },
  {
    id: 6,
    nama_obat: "Amoxicillin",
    nama_obat_internasional: "Amoxicillin",
    display_name: "Amoxicillin (Amoxicillin)",
  },
  {
    id: 7,
    nama_obat: "Omeprazole",
    nama_obat_internasional: "Omeprazole",
    display_name: "Omeprazole (Omeprazole)",
  },
  {
    id: 8,
    nama_obat: "Amlodipine",
    nama_obat_internasional: "Amlodipine",
    display_name: "Amlodipine (Amlodipine)",
  },
  {
    id: 9,
    nama_obat: "Simvastatin",
    nama_obat_internasional: "Simvastatin",
    display_name: "Simvastatin (Simvastatin)",
  },
  {
    id: 10,
    nama_obat: "Captopril",
    nama_obat_internasional: "Captopril",
    display_name: "Captopril (Captopril)",
  },
  {
    id: 11,
    nama_obat: "Atorvastatin",
    nama_obat_internasional: "Atorvastatin",
    display_name: "Atorvastatin (Atorvastatin)",
  },
  {
    id: 12,
    nama_obat: "Gliclazide",
    nama_obat_internasional: "Gliclazide",
    display_name: "Gliclazide (Gliclazide)",
  },
  {
    id: 13,
    nama_obat: "Digoxin",
    nama_obat_internasional: "Digoxin",
    display_name: "Digoxin (Digoxin)",
  },
  {
    id: 14,
    nama_obat: "Salbutamol",
    nama_obat_internasional: "Salbutamol",
    display_name: "Salbutamol (Salbutamol)",
  },
  {
    id: 15,
    nama_obat: "Tamsulosin",
    nama_obat_internasional: "Tamsulosin",
    display_name: "Tamsulosin (Tamsulosin)",
  },
];

export const mockDrugInteractions = [
  {
    drug_a: "Warfarin",
    drug_b: "Ibuprofen",
    severity: "Major",
    description:
      "Meningkatkan risiko perdarahan secara signifikan akibat sinergisme antikoagulan dengan antiplatelet.",
    recommendation:
      "Hindari penggunaan bersamaan. Gunakan paracetamol sebagai alternatif analgesik. Jika harus digunakan bersamaan, monitor INR ketat.",
    mechanism:
      "Warfarin menghambat sintesis faktor koagulasi, sementara ibuprofen menghambat agregasi platelet.",
    clinical_effect:
      "Peningkatan risiko perdarahan mayor terutama gastrointestinal dan intrakranial.",
  },
  {
    drug_a: "Warfarin",
    drug_b: "Paracetamol",
    severity: "Minor",
    description:
      "Paracetamol dosis tinggi dapat sedikit meningkatkan efek warfarin.",
    recommendation:
      "Monitor INR jika penggunaan paracetamol jangka panjang atau dosis tinggi (>2g/hari).",
    mechanism:
      "Kemungkinan inhibisi metabolisme warfarin oleh paracetamol pada dosis tinggi.",
    clinical_effect:
      "Peningkatan ringan efek antikoagulan pada penggunaan jangka panjang.",
  },
  {
    drug_a: "Metformin",
    drug_b: "Lisinopril",
    severity: "Moderate",
    description:
      "ACE inhibitor dapat meningkatkan sensitivitas insulin dan memperkuat efek hipoglikemik metformin.",
    recommendation:
      "Monitor gula darah lebih ketat terutama 2-4 minggu awal kombinasi. Edukasi pasien tentang gejala hipoglikemia.",
    mechanism:
      "ACE inhibitor meningkatkan sensitivitas insulin dan uptake glukosa perifer.",
    clinical_effect:
      "Peningkatan risiko hipoglikemia terutama pada pasien dengan fungsi ginjal terganggu.",
  },
  {
    drug_a: "Digoxin",
    drug_b: "Amiodarone",
    severity: "Major",
    description:
      "Amiodarone meningkatkan kadar digoxin dalam darah secara signifikan.",
    recommendation:
      "Kurangi dosis digoxin 50% saat memulai amiodarone. Monitor kadar digoxin dan gejala toksisitas.",
    mechanism:
      "Amiodarone menghambat eliminasi digoxin melalui inhibisi P-glikoprotein.",
    clinical_effect:
      "Peningkatan kadar digoxin hingga 70% dengan risiko toksisitas digoxin.",
  },
];

// Export default untuk backward compatibility
export default {
  mockPatients,
  mockICD10,
  mockDrugs,
  mockDrugInteractions,
};
