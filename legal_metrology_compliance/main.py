import os
import argparse
from dotenv import load_dotenv

# Automatically load API keys from .env file
load_dotenv()

from src.pdf_parser import LegalPDFParser
from src.legal_synthesizer import LegalSynthesizer
from src.human_pdf_generator import HumanPDFGenerator
from src.machine_schema_generator import MachineSchemaGenerator

def run_pipeline(input_dir, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    
    print("=" * 70)
    print("      MODULE 1: LEGAL METROLOGY PDF CONSOLIDATION ENGINE")
    print("=" * 70)
    print(f"Input Directory:  {input_dir}")
    print(f"Output Directory: {output_dir}\n")

    parser = LegalPDFParser()
    synthesizer = LegalSynthesizer()

    # Step 1: Scan and parse input PDFs
    pdf_files = [f for f in os.listdir(input_dir) if f.lower().endswith('.pdf')]
    if not pdf_files:
        print(f"[ERROR] No PDF files found in {input_dir}. Please place legal PDFs there.")
        return

    parsed_docs = []
    print(f"Found {len(pdf_files)} legal PDF(s) to process:")
    for pdf_file in sorted(pdf_files):
        pdf_path = os.path.join(input_dir, pdf_file)
        print(f"  -> Parsing: {pdf_file}...")
        doc_info = parser.parse_pdf(pdf_path)
        parsed_docs.append(doc_info)
        
        # Step 2: Feed parsed text into Synthesizer
        synthesizer.process_document(doc_info)

    # Step 3: Get consolidated state
    consolidated_rules = synthesizer.get_consolidated_state()
    print(f"\n[SUCCESS] Synthesized {len(consolidated_rules)} master legal rule specifications.")

    # Step 4: Generate Human-Readable PDF
    human_pdf_path = os.path.join(output_dir, "Consolidated_Legal_Metrology_Rulebook_Human.pdf")
    human_gen = HumanPDFGenerator(human_pdf_path)
    human_gen.generate_pdf(consolidated_rules, parsed_docs)

    # Step 5: Generate Machine-Readable JSON & PDF Specification
    machine_json_path = os.path.join(output_dir, "rules_knowledge_base.json")
    machine_pdf_path = os.path.join(output_dir, "Machine_Rules_Specification.pdf")
    machine_gen = MachineSchemaGenerator(machine_json_path, machine_pdf_path)
    machine_gen.generate_schema(consolidated_rules)

    print("\n" + "=" * 70)
    print("                 SUMMARY OF GENERATED ARTIFACTS")
    print("=" * 70)
    print(f" 1. Human Legal Rulebook PDF:  {human_pdf_path}")
    print(f" 2. Machine JSON Database:     {machine_json_path}")
    print(f" 3. Machine PDF Specification: {machine_pdf_path}")
    print("=" * 70 + "\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Legal Metrology PDF Rule Consolidator")
    parser.add_argument("--input_dir", default="./input_pdfs", help="Directory containing input legal PDFs")
    parser.add_argument("--output_dir", default="./output", help="Directory to save generated outputs")
    args = parser.parse_args()

    base_dir = os.path.dirname(os.path.abspath(__file__))
    input_path = os.path.join(base_dir, args.input_dir) if not os.path.isabs(args.input_dir) else args.input_dir
    output_path = os.path.join(base_dir, args.output_dir) if not os.path.isabs(args.output_dir) else args.output_dir

    run_pipeline(input_path, output_path)
