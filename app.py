
import streamlit as st
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table,
    TableStyle, Image, KeepTogether
)
from reportlab.lib.units import mm
from xml.sax.saxutils import escape
from io import BytesIO
from datetime import date
import statistics


# --------------------------------------------------
# 1. APPLICATION CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="NDE Inspection Report Generator",
    page_icon="🔍",
    layout="wide"
)

st.title("NDE Inspection Report Generator")
st.caption(
    "Non-Destructive Examination | Inspection Documentation System"
)

st.info(
    "This application prepares inspection documentation. "
    "Final technical acceptance must be determined by qualified "
    "personnel using the applicable inspection procedure and criteria."
)


# --------------------------------------------------
# 2. INPUT VALIDATION
# --------------------------------------------------

def validate(data):
    errors = []

    required_fields = {
        "Report Number": data["report_no"],
        "Client": data["client"],
        "Component": data["component"],
        "Material": data["material"],
        "Inspector": data["inspector"],
        "Inspection Procedure": data["procedure"],
        "Observations": data["observations"]
    }

    for field, value in required_fields.items():
        if not str(value).strip():
            errors.append(f"{field} is required.")

    if data["technique"] == "Ultrasonic Testing (UT)":
        if not data["readings"]:
            errors.append("Enter at least one UT thickness reading.")

        if any(value <= 0 for value in data["readings"]):
            errors.append("Thickness readings must be positive.")

    if data["previous_thickness"] is not None:
        if data["previous_thickness"] <= 0:
            errors.append("Previous thickness must be positive.")

    if data["service_years"] is not None:
        if data["service_years"] <= 0:
            errors.append("Service duration must be greater than zero.")

    if (data["previous_thickness"] is None) != (
        data["service_years"] is None
    ):
        errors.append(
            "Enter both previous thickness and service duration "
            "for corrosion-rate calculation."
        )

    if (
        data["previous_thickness"] is not None
        and data["readings"]
        and data["previous_thickness"] < min(data["readings"])
    ):
        errors.append(
            "Previous thickness is lower than the current minimum "
            "reading. Verify the input data."
        )

    return errors


# --------------------------------------------------
# 3. ENGINEERING CALCULATIONS
# --------------------------------------------------

def calculate(data):

    results = {
        "technique": data["technique"]
    }

    if data["technique"] == "Ultrasonic Testing (UT)":

        readings = data["readings"]

        average = statistics.mean(readings)
        minimum = min(readings)
        maximum = max(readings)

        results["average_thickness"] = average
        results["minimum_thickness"] = minimum
        results["maximum_thickness"] = maximum

        if data["previous_thickness"] is not None:

            corrosion_loss = (
                data["previous_thickness"] - average
            )

            corrosion_rate = (
                corrosion_loss / data["service_years"]
            )

            results["corrosion_loss"] = corrosion_loss
            results["corrosion_rate"] = corrosion_rate

    return results


# --------------------------------------------------
# 4. PDF REPORT GENERATION
# --------------------------------------------------

def build_pdf(data, results):

    buffer = BytesIO()

    pdf = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontSize=17,
        spaceAfter=8
    )

    heading_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        textColor=colors.HexColor("#17365D"),
        spaceBefore=12,
        spaceAfter=6
    )

    normal_style = styles["BodyText"]

    story = []

    story.append(
        Paragraph("NDE INSPECTION REPORT", title_style)
    )

    story.append(
        Paragraph(
            "NON-DESTRUCTIVE EXAMINATION RECORD",
            ParagraphStyle(
                "Subtitle",
                parent=normal_style,
                alignment=TA_CENTER
            )
        )
    )

    story.append(Spacer(1, 12))

    def safe(value):
        return escape(str(value if value not in (None, "") else "Not provided"))

    def add_table(rows, widths=None):

        table = Table(
            rows,
            colWidths=widths,
            repeatRows=1
        )

        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0),
             colors.HexColor("#17365D")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1),
             [colors.white, colors.HexColor("#EDF2F7")]),
            ("LEFTPADDING", (0, 0), (-1, -1), 7),
            ("RIGHTPADDING", (0, 0), (-1, -1), 7),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6)
        ]))

        story.append(table)
        story.append(Spacer(1, 8))

    story.append(Paragraph("1. GENERAL INFORMATION", heading_style))

    add_table([
        ["Parameter", "Inspection Details"],
        ["Report Number", safe(data["report_no"])],
        ["Inspection Date", safe(data["inspection_date"])],
        ["Client", safe(data["client"])],
        ["Component", safe(data["component"])],
        ["Location", safe(data["location"])],
        ["Material", safe(data["material"])],
        ["Drawing / Identification", safe(data["drawing"])],
        ["Inspector", safe(data["inspector"])]
    ], [65 * mm, 105 * mm])

    story.append(Paragraph("2. INSPECTION DETAILS", heading_style))

    add_table([
        ["Parameter", "Details"],
        ["NDE Technique", safe(data["technique"])],
        ["Procedure", safe(data["procedure"])],
        ["Applicable Standard", safe(data["standard"])],
        ["Equipment", safe(data["equipment"])],
        ["Calibration Details", safe(data["calibration"])],
        ["Inspection Coverage", safe(data["coverage"])]
    ], [65 * mm, 105 * mm])

    story.append(Paragraph("3. INSPECTION OBSERVATIONS", heading_style))

    story.append(
        Paragraph(
            safe(data["observations"]),
            normal_style
        )
    )

    story.append(Spacer(1, 8))

    story.append(
        Paragraph("4. INDICATIONS AND FINDINGS", heading_style)
    )

    story.append(
        Paragraph(
            safe(data["indications"]),
            normal_style
        )
    )

    if data["technique"] == "Ultrasonic Testing (UT)":

        story.append(
            Paragraph("5. UT MEASUREMENTS AND CALCULATIONS", heading_style)
        )

        measurement_rows = [
            ["Measurement", "Result"],
            [
                "Thickness readings (mm)",
                ", ".join(f"{x:.2f}" for x in data["readings"])
            ],
            [
                "Average thickness (mm)",
                f"{results['average_thickness']:.3f}"
            ],
            [
                "Minimum thickness (mm)",
                f"{results['minimum_thickness']:.3f}"
            ],
            [
                "Maximum thickness (mm)",
                f"{results['maximum_thickness']:.3f}"
            ]
        ]

        if "corrosion_rate" in results:

            measurement_rows.extend([
                [
                    "Previous thickness (mm)",
                    f"{data['previous_thickness']:.3f}"
                ],
                [
                    "Average thickness loss (mm)",
                    f"{results['corrosion_loss']:.3f}"
                ],
                [
                    "Service duration (years)",
                    f"{data['service_years']:.2f}"
                ],
                [
                    "Average thickness loss rate (mm/year)",
                    f"{results['corrosion_rate']:.4f}"
                ]
            ])

        add_table(measurement_rows, [85 * mm, 85 * mm])

        story.append(
            Paragraph(
                "Calculation note: Average thickness loss rate is "
                "calculated as (previous thickness - current average "
                "thickness) / service duration. This is an indicative "
                "historical average, not a validated future corrosion "
                "prediction or remaining-life assessment.",
                normal_style
            )
        )

    story.append(Spacer(1, 10))

    if data["photo"] is not None:

        story.append(
            Paragraph("INSPECTION PHOTOGRAPH", heading_style)
        )

        try:
            photo = Image(
                BytesIO(data["photo"]),
                width=150 * mm,
                height=90 * mm,
                kind="proportional"
            )
            story.append(photo)
        except Exception:
            story.append(
                Paragraph("Photograph could not be embedded.", normal_style)
            )

    story.append(
        Paragraph("6. INSPECTION RECORD", heading_style)
    )

    add_table([
        ["Field", "Recorded Information"],
        ["Recorded Disposition", safe(data["disposition"])],
        ["Inspector Remarks", safe(data["remarks"])],
        ["Prepared By", safe(data["inspector"])],
        ["Review Status", "Pending qualified technical review"]
    ], [65 * mm, 105 * mm])

    story.append(
        Paragraph("7. LIMITATIONS AND DISCLAIMER", heading_style)
    )

    story.append(
        Paragraph(
            "This report is a record of the information entered into "
            "the application. The software does not interpret raw NDE "
            "signals, independently establish defect acceptance limits, "
            "certify equipment fitness, or replace qualified inspection. "
            "All findings and dispositions must be reviewed against "
            "the applicable code, standard and approved procedure.",
            normal_style
        )
    )

    story.append(Spacer(1, 20))

    story.append(
        Paragraph(
            "End of Inspection Report",
            ParagraphStyle(
                "Footer",
                parent=normal_style,
                alignment=TA_CENTER
            )
        )
    )

    pdf.build(story)

    buffer.seek(0)

    return buffer.getvalue()


# --------------------------------------------------
# 5. APPLICATION INTERFACE
# --------------------------------------------------

st.header("Inspection Data Entry")

with st.form("nde_inspection_form"):

    st.subheader("A. General Information")

    col1, col2 = st.columns(2)

    with col1:
        report_no = st.text_input("Report Number")
        client = st.text_input("Client / Organisation")
        component = st.text_input("Component / Equipment")
        material = st.text_input("Material")

    with col2:
        inspection_date = st.date_input(
            "Inspection Date",
            value=date.today()
        )
        location = st.text_input("Inspection Location")
        drawing = st.text_input("Drawing / Component ID")
        inspector = st.text_input("Inspector Name")

    st.divider()

    st.subheader("B. NDE Inspection Details")

    technique = st.selectbox(
        "Select NDE Technique",
        [
            "Ultrasonic Testing (UT)",
            "Radiographic Testing (RT)",
            "Magnetic Particle Testing (MT)",
            "Liquid Penetrant Testing (PT)",
            "Visual Testing (VT)"
        ]
    )

    col3, col4 = st.columns(2)

    with col3:
        procedure = st.text_input("Inspection Procedure")
        standard = st.text_input("Applicable Code / Standard")

    with col4:
        equipment = st.text_input("Equipment Used")
        calibration = st.text_input("Calibration Details")

    coverage = st.text_area(
        "Inspection Coverage / Area Examined"
    )

    st.divider()

    st.subheader("C. Inspection Observations")

    observations = st.text_area(
        "Inspection Observations",
        placeholder="Describe the inspection observations..."
    )

    indications = st.text_area(
        "Indications / Findings",
        placeholder="Record location, type, dimensions and relevant details..."
    )

    st.divider()

    st.subheader("D. UT Measurements")

    st.caption(
        "These measurements are applicable only to Ultrasonic Testing."
    )

    readings_text = st.text_input(
        "Thickness Readings in mm (comma separated)",
        placeholder="Example: 9.8, 9.7, 9.6, 9.9"
    )

    col5, col6 = st.columns(2)

    with col5:
        previous_text = st.text_input(
            "Previous Thickness (mm)",
            placeholder="Optional"
        )

    with col6:
        years_text = st.text_input(
            "Service Duration (years)",
            placeholder="Optional"
        )

    st.divider()

    st.subheader("E. Inspection Record")

    disposition = st.selectbox(
        "Recorded Disposition",
        [
            "Pending technical review",
            "No relevant indications reported",
            "Indications recorded for evaluation",
            "Further examination required"
        ]
    )

    remarks = st.text_area("Additional Remarks")

    photo_file = st.file_uploader(
        "Upload Inspection Photograph (Optional)",
        type=["jpg", "jpeg", "png"]
    )

    submitted = st.form_submit_button(
        "Validate and Generate Inspection Report",
        type="primary",
        use_container_width=True
    )


# --------------------------------------------------
# 6. PROCESSING AND REPORT DOWNLOAD
# --------------------------------------------------

if submitted:

    errors = []

    readings = []

    try:
        if readings_text.strip():
            readings = [
                float(x.strip())
                for x in readings_text.split(",")
                if x.strip()
            ]

            if len(readings) != len([
                x for x in readings_text.split(",") if x.strip()
            ]):
                errors.append("Invalid thickness reading.")

    except ValueError:
        errors.append(
            "Thickness readings must contain valid numbers."
        )

    try:
        previous = (
            float(previous_text)
            if previous_text.strip()
            else None
        )
    except ValueError:
        previous = None
        errors.append("Previous thickness must be numeric.")

    try:
        years = (
            float(years_text)
            if years_text.strip()
            else None
        )
    except ValueError:
        years = None
        errors.append("Service duration must be numeric.")

    data = {
        "report_no": report_no,
        "inspection_date": str(inspection_date),
        "client": client,
        "component": component,
        "material": material,
        "location": location,
        "drawing": drawing,
        "inspector": inspector,
        "technique": technique,
        "procedure": procedure,
        "standard": standard,
        "equipment": equipment,
        "calibration": calibration,
        "coverage": coverage,
        "observations": observations,
        "indications": indications,
        "readings": readings,
        "previous_thickness": previous,
        "service_years": years,
        "disposition": disposition,
        "remarks": remarks,
        "photo": photo_file.getvalue() if photo_file else None
    }

    if not errors:
        errors.extend(validate(data))

    if errors:

        st.error("Please correct the following issues:")

        for error in errors:
            st.write("• " + error)

    else:

        results = calculate(data)

        st.success("Input validation successful.")

        st.subheader("Calculation Results")

        if "average_thickness" in results:

            c1, c2, c3 = st.columns(3)

            c1.metric(
                "Average Thickness",
                f"{results['average_thickness']:.3f} mm"
            )

            c2.metric(
                "Minimum Thickness",
                f"{results['minimum_thickness']:.3f} mm"
            )

            c3.metric(
                "Maximum Thickness",
                f"{results['maximum_thickness']:.3f} mm"
            )

            if "corrosion_rate" in results:

                st.metric(
                    "Average Thickness Loss Rate",
                    f"{results['corrosion_rate']:.4f} mm/year"
                )

        pdf_file = build_pdf(data, results)

        st.success("Inspection report generated successfully.")

        st.download_button(
            label="Download NDE Inspection Report (PDF)",
            data=pdf_file,
            file_name=f"{report_no}_NDE_Report.pdf",
            mime="application/pdf",
            use_container_width=True
        )


# --------------------------------------------------
# 7. APPLICATION FOOTER
# --------------------------------------------------

st.divider()

st.caption(
    "NDE Inspection Report Generator | Academic Mechanical "
    "Engineering Project"
)
