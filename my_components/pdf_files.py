# 🔹 PDF Function
def save_to_simple_pdf(filename="query_result.pdf"):
    # Step 1: Call LLM
    final_result = run_llm("pdf", instructions=task_instruction)

    # Step 2: Create PDF
    doc = SimpleDocTemplate(filename, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    story.append(
        Paragraph(f"<b><font size='16'>Answer:</font></b>", styles["Heading1"])
    )
    formatted_answer = final_result.replace("\n", "<br/>")
    story.append(Paragraph(formatted_answer, styles["Normal"]))
    story.append(Spacer(1, 20))
    story.append(
        Paragraph(
            f"<i>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>",
            styles["Italic"],
        )
    )

    doc.build(story)
    print(f"✅ PDF saved: {filename}")


# 🔹 Usage
my_file = input("Enter the name of your file: ")
# task_instruction = "extract the text from page number 3 of given pdf..."
save_to_simple_pdf(
    f"../my_pdf_files/{my_file}.pdf",
)
