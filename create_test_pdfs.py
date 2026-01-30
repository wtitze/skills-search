from fpdf import FPDF
import os

# Creazione cartella di output
os.makedirs("test_material", exist_ok=True)

def create_pdf(filename, content, title="Documento Tecnico"):
    pdf = FPDF()
    pdf.add_page()
    # Usiamo Helvetica (font standard) per evitare DeprecationWarning
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(190, 10, title, ln=True, align='C')
    pdf.ln(10)
    
    pdf.set_font("Helvetica", size=12)
    # Definiamo una larghezza fissa (190mm) per evitare errori di calcolo spazio
    for line in content.split('\n'):
        if line.strip():
            pdf.multi_cell(190, 8, line)
        else:
            pdf.ln(4)
            
    pdf.output(f"test_material/{filename}")

# --- 1. GENERAZIONE 15 CV ---
sedi = {
    "Milano": [
        ("Marco Rossi", "Senior Frontend Developer. Esperto React e Next.js."),
        ("Luca Bianchi", "Backend Engineer. Specialista Node.js e microservizi."),
        ("Giulia Verdi", "Android Developer. Esperta Kotlin e Jetpack Compose."),
        ("Alessandro Neri", "iOS Developer. Esperto Swift e SwiftUI."),
        ("Sofia Russo", "Penetration Tester. Esperta Kali Linux e Metasploit.")
    ],
    "Singapore": [
        ("Chen Wei", "Frontend Specialist. Esperto Angular."),
        ("Siti Aminah", "Python Backend Developer. Esperta Django e AI Integration."),
        ("Arjun Mehta", "Mobile Cross-Platform. Esperto Flutter."),
        ("Li Na", "Senior iOS Engineer. Esperta Swift e sicurezza bancaria."),
        ("Kevin Tan", "Cybersecurity Analyst. Esperto AWS e SIEM.")
    ],
    "New York": [
        ("John Smith", "Fullstack Developer. Esperto React e Go."),
        ("Sarah Johnson", "Java Backend Expert. Esperta Spring Boot e Kafka."),
        ("Michael Brown", "Android Lead. Esperto Firebase."),
        ("Emily Davis", "Mobile Architect. Esperta React Native."),
        ("Robert Wilson", "Cloud Security. Esperto Azure Security ed audit Microsoft.")
    ]
}

for sede, persone in sedi.items():
    for nome, desc in persone:
        filename = f"cv_{sede.lower()}_{nome.replace(' ', '_').lower()}.pdf"
        create_pdf(filename, f"NOME COMPLETO: {nome}\nSEDE DI LAVORO: {sede}\n\nPROFILO PROFESSIONALE:\n{desc}", title=f"Curriculum Vitae - {nome}")

# --- 2. PRESENTAZIONE TECNICA (Senza nome di Marco Rossi nel testo) ---
pqc_content = """ANALISI DEI SISTEMI DI CONTROLLO SATELLITARE LEO

Slide 1: Introduzione
Gestione della telemetria in tempo reale per costellazioni di microsatelliti.

Slide 2: Comunicazioni Ka-Band
Integrazione di protocolli di correzione d'errore (Forward Error Correction).

Slide 3: Prevenzione Collisioni
Algoritmi di intelligenza artificiale per il calcolo delle traiettorie di evasione detriti spaziali."""

create_pdf("presentazione_satelliti.pdf", pqc_content, title="Ricerca Interna: Sistemi Satellitari")

# --- 3. CERTIFICATO TECNICO (Per Sarah Johnson) ---
cert_content = """ATTESTATO DI COMPETENZA PROFESSIONALE

Si certifica che la dipendente SARAH JOHNSON ha completato con successo il percorso formativo avanzato in:
ARCHITETTURE BLOCKCHAIN AZIENDALI (Hyperledger Fabric)

Data: 15 Dicembre 2024
Valutazione: Eccellente"""

create_pdf("certificato_blockchain_johnson.pdf", cert_content, title="Certificazione Tecnica")

print("SUCCESSO: 17 file PDF generati correttamente in 'test_material/'")
