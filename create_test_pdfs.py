from fpdf import FPDF
import os

# Forza la creazione della cartella
os.makedirs("test_material", exist_ok=True)

def create_pro_pdf(filename, content, title):
    # Inizializzazione moderna
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_margins(20, 20, 20)
    pdf.add_page()
    
    # Intestazione Standard
    pdf.set_font("helvetica", "B", 10)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(0, 10, "DOCUMENTO AZIENDALE RISERVATO", new_x="LMARGIN", new_y="NEXT", align="C")
    
    # Titolo principale
    pdf.ln(5)
    pdf.set_font("helvetica", "B", 18)
    pdf.set_text_color(30, 41, 59)
    pdf.cell(0, 15, title.upper(), new_x="LMARGIN", new_y="NEXT", align="L")
    
    # Linea estetica
    pdf.set_draw_color(30, 41, 59)
    pdf.line(20, pdf.get_y(), 190, pdf.get_y())
    pdf.ln(10)
    
    # Corpo del testo (GESTIONE AUTOMATICA)
    pdf.set_font("helvetica", "", 12)
    pdf.set_text_color(0, 0, 0)
    
    # Passiamo l'intero blocco di testo a multi_cell: pensa lui a tutto
    # w=0 significa "usa tutta la larghezza tra i margini"
    pdf.multi_cell(w=0, h=8, text=content, align="L")
            
    pdf.output(f"test_material/{filename}")

# --- DATASET ---
sedi = {
    "Milano": [
        ("Marco Rossi", "Senior Frontend Developer. Esperto React e Next.js. 8 anni di esperienza."),
        ("Luca Bianchi", "Backend Engineer. Specialista Node.js, microservizi e Docker."),
        ("Giulia Verdi", "Android Developer. Esperta Kotlin e Jetpack Compose."),
        ("Alessandro Neri", "iOS Developer. Esperto Swift e SwiftUI."),
        ("Sofia Russo", "Penetration Tester. Esperta Kali Linux e Metasploit.")
    ],
    "Singapore": [
        ("Chen Wei", "Frontend Specialist. Esperto Angular e RxJS."),
        ("Siti Aminah", "Python Backend Developer. Esperta Django e AI Integration."),
        ("Arjun Mehta", "Mobile Cross-Platform. Esperto Flutter e Dart."),
        ("Li Na", "Senior iOS Engineer. Esperta Swift e sicurezza bancaria."),
        ("Kevin Tan", "Cybersecurity Analyst. Esperto AWS e SIEM.")
    ],
    "New York": [
        ("John Smith", "Fullstack Developer. Esperto React e linguaggio Go."),
        ("Sarah Johnson", "Java Backend Expert. Esperta Spring Boot e Kafka."),
        ("Michael Brown", "Android Lead. Esperto Firebase e Studio."),
        ("Emily Davis", "Mobile Architect. Esperta React Native."),
        ("Robert Wilson", "Cloud Security. Esperto Azure Security ed audit Microsoft.")
    ]
}

# Generazione 15 CV
for sede, persone in sedi.items():
    for nome, desc in persone:
        f_name = f"cv_{sede.lower().replace(' ', '_')}_{nome.lower().replace(' ', '_')}.pdf"
        body = f"DIPENDENTE: {nome}\nSEDE: {sede}\n\nPROFILO PROFESSIONALE:\n{desc}"
        create_pro_pdf(f_name, body, "Curriculum Vitae")

# Generazione Documento Tecnico
sat_text = "ARGOMENTO: SISTEMI SATELLITARI LEO\nAUTORE: Marco Rossi\n\nCONTENUTI:\n- Analisi telemetria satellitare.\n- Protocolli Ka-Band.\n- Algoritmi AI per droni e satelliti."
create_pro_pdf("presentazione_satelliti.pdf", sat_text, "Ricerca Tecnica")

# Generazione Certificato
cert_text = "CERTIFICAZIONE PROFESSIONALE\n\nSi attesta che SARAH JOHNSON ha completato il corso:\nBLOCKCHAIN ARCHITECT - HYPERLEDGER FABRIC.\nData rilascio: Dicembre 2024."
create_pro_pdf("certificato_blockchain.pdf", cert_text, "Certificato Tecnico")

print("17 PDF generati con successo in 'test_material/' senza errori di formattazione.")
