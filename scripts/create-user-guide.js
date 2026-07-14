const fs = require('fs');
const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
        Header, Footer, AlignmentType, HeadingLevel, BorderStyle, WidthType,
        ShadingType, PageNumber, PageBreak, LevelFormat, TabStopType, TabStopPosition } = require('docx');

const PRIMARY = "1B4F72";
const SECONDARY = "2E86C1";
const ACCENT = "85C1E9";
const DARK = "1A1A1A";
const LIGHT = "EBF5FB";
const WHITE = "FFFFFF";
const WARNING = "F39C12";
const SUCCESS = "27AE60";

const border = { style: BorderStyle.SINGLE, size: 1, color: "D5D8DC" };
const borders = { top: border, bottom: border, left: border, right: border };
const cellMargins = { top: 100, bottom: 100, left: 150, right: 150 };

const doc = new Document({
  styles: {
    default: { document: { run: { font: "Arial", size: 22, color: DARK } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 36, bold: true, font: "Arial", color: PRIMARY },
        paragraph: { spacing: { before: 360, after: 200 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 28, bold: true, font: "Arial", color: SECONDARY },
        paragraph: { spacing: { before: 280, after: 160 }, outlineLevel: 1 } },
      { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 24, bold: true, font: "Arial", color: PRIMARY },
        paragraph: { spacing: { before: 200, after: 120 }, outlineLevel: 2 } },
    ]
  },
  numbering: {
    config: [
      { reference: "bullets",
        levels: [{ level: 0, format: LevelFormat.BULLET, text: "\u2022", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
      { reference: "numbers",
        levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
      { reference: "steps",
        levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "Step %1:", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 720 } } } }] },
    ]
  },
  sections: [
    // === COVER PAGE ===
    {
      properties: {
        page: {
          size: { width: 12240, height: 15840 },
          margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 }
        }
      },
      children: [
        new Paragraph({ spacing: { before: 3000 }, children: [] }),
        new Paragraph({
          alignment: AlignmentType.CENTER,
          spacing: { after: 200 },
          children: [new TextRun({ text: "HOSPITAL HEALTH", size: 56, bold: true, font: "Arial", color: PRIMARY })]
        }),
        new Paragraph({
          alignment: AlignmentType.CENTER,
          spacing: { after: 200 },
          children: [new TextRun({ text: "MANAGEMENT SYSTEM", size: 56, bold: true, font: "Arial", color: PRIMARY })]
        }),
        new Paragraph({
          alignment: AlignmentType.CENTER,
          spacing: { after: 400 },
          border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: SECONDARY, space: 1 } },
          children: [new TextRun({ text: " ", size: 12 })]
        }),
        new Paragraph({
          alignment: AlignmentType.CENTER,
          spacing: { after: 100 },
          children: [new TextRun({ text: "User Guide", size: 36, italic: true, color: SECONDARY })]
        }),
        new Paragraph({
          alignment: AlignmentType.CENTER,
          spacing: { after: 100 },
          children: [new TextRun({ text: "Comprehensive Usage Instructions", size: 24, color: "5D6D7E" })]
        }),
        new Paragraph({ spacing: { before: 2000 }, children: [] }),
        new Paragraph({
          alignment: AlignmentType.CENTER,
          spacing: { after: 100 },
          children: [new TextRun({ text: "Version 1.0", size: 22, color: "5D6D7E" })]
        }),
        new Paragraph({
          alignment: AlignmentType.CENTER,
          spacing: { after: 100 },
          children: [new TextRun({ text: "July 2026", size: 22, color: "5D6D7E" })]
        }),
        new Paragraph({
          alignment: AlignmentType.CENTER,
          children: [new TextRun({ text: "DKEEMZ Technologies", size: 20, color: "ABB2B9" })]
        }),
      ]
    },

    // === TABLE OF CONTENTS ===
    {
      properties: {
        page: {
          size: { width: 12240, height: 15840 },
          margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 }
        }
      },
      headers: {
        default: new Header({
          children: [new Paragraph({
            border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: SECONDARY, space: 1 } },
            children: [
              new TextRun({ text: "HMS User Guide", font: "Arial", size: 18, color: "5D6D7E" }),
              new TextRun({ text: "\t", children: [] }),
              new TextRun({ text: "Version 1.0", font: "Arial", size: 18, color: "5D6D7E", italics: true }),
            ],
            tabStops: [{ type: TabStopType.RIGHT, position: TabStopPosition.MAX }],
          })]
        })
      },
      footers: {
        default: new Footer({
          children: [new Paragraph({
            alignment: AlignmentType.CENTER,
            border: { top: { style: BorderStyle.SINGLE, size: 4, color: ACCENT, space: 1 } },
            children: [
              new TextRun({ text: "DKEEMZ Technologies  |  Page ", size: 18, color: "5D6D7E" }),
              new TextRun({ children: [PageNumber.CURRENT], size: 18, color: "5D6D7E" }),
            ]
          })]
        })
      },
      children: [
        new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("Table of Contents")] }),
        new Paragraph({ spacing: { after: 100 }, children: [new TextRun({ text: "1. Getting Started", bold: true, size: 22 })] }),
        new Paragraph({ spacing: { after: 100 }, indent: { left: 360 }, children: [new TextRun("1.1 System Requirements")] }),
        new Paragraph({ spacing: { after: 100 }, indent: { left: 360 }, children: [new TextRun("1.2 First-Time Login")] }),
        new Paragraph({ spacing: { after: 100 }, indent: { left: 360 }, children: [new TextRun("1.3 Setting Up MFA")] }),
        new Paragraph({ spacing: { after: 200 }, indent: { left: 360 }, children: [new TextRun("1.4 Dashboard Overview")] }),

        new Paragraph({ spacing: { after: 100 }, children: [new TextRun({ text: "2. Patient Management", bold: true, size: 22 })] }),
        new Paragraph({ spacing: { after: 100 }, indent: { left: 360 }, children: [new TextRun("2.1 Registering a New Patient")] }),
        new Paragraph({ spacing: { after: 100 }, indent: { left: 360 }, children: [new TextRun("2.2 Searching for Patients")] }),
        new Paragraph({ spacing: { after: 100 }, indent: { left: 360 }, children: [new TextRun("2.3 Viewing Patient Records")] }),
        new Paragraph({ spacing: { after: 200 }, indent: { left: 360 }, children: [new TextRun("2.4 Updating Patient Information")] }),

        new Paragraph({ spacing: { after: 100 }, children: [new TextRun({ text: "3. Appointment Scheduling", bold: true, size: 22 })] }),
        new Paragraph({ spacing: { after: 100 }, indent: { left: 360 }, children: [new TextRun("3.1 Creating an Appointment")] }),
        new Paragraph({ spacing: { after: 100 }, indent: { left: 360 }, children: [new TextRun("3.2 Viewing the Calendar")] }),
        new Paragraph({ spacing: { after: 100 }, indent: { left: 360 }, children: [new TextRun("3.3 Rescheduling Appointments")] }),
        new Paragraph({ spacing: { after: 200 }, indent: { left: 360 }, children: [new TextRun("3.4 Canceling Appointments")] }),

        new Paragraph({ spacing: { after: 100 }, children: [new TextRun({ text: "4. Electronic Health Records", bold: true, size: 22 })] }),
        new Paragraph({ spacing: { after: 100 }, indent: { left: 360 }, children: [new TextRun("4.1 Creating a New Encounter")] }),
        new Paragraph({ spacing: { after: 100 }, indent: { left: 360 }, children: [new TextRun("4.2 Recording Vitals")] }),
        new Paragraph({ spacing: { after: 100 }, indent: { left: 360 }, children: [new TextRun("4.3 Writing Clinical Notes")] }),
        new Paragraph({ spacing: { after: 100 }, indent: { left: 360 }, children: [new TextRun("4.4 Managing Problem Lists")] }),
        new Paragraph({ spacing: { after: 100 }, indent: { left: 360 }, children: [new TextRun("4.5 Prescribing Medications")] }),
        new Paragraph({ spacing: { after: 200 }, indent: { left: 360 }, children: [new TextRun("4.6 Ordering Lab Tests")] }),

        new Paragraph({ spacing: { after: 100 }, children: [new TextRun({ text: "5. Billing & Invoicing", bold: true, size: 22 })] }),
        new Paragraph({ spacing: { after: 100 }, indent: { left: 360 }, children: [new TextRun("5.1 Generating Invoices")] }),
        new Paragraph({ spacing: { after: 100 }, indent: { left: 360 }, children: [new TextRun("5.2 Processing Payments")] }),
        new Paragraph({ spacing: { after: 200 }, indent: { left: 360 }, children: [new TextRun("5.3 Insurance Claims")] }),

        new Paragraph({ spacing: { after: 100 }, children: [new TextRun({ text: "6. Administration", bold: true, size: 22 })] }),
        new Paragraph({ spacing: { after: 100 }, indent: { left: 360 }, children: [new TextRun("6.1 Managing Users")] }),
        new Paragraph({ spacing: { after: 100 }, indent: { left: 360 }, children: [new TextRun("6.2 Role-Based Access Control")] }),
        new Paragraph({ spacing: { after: 100 }, indent: { left: 360 }, children: [new TextRun("6.3 Audit Logs")] }),
        new Paragraph({ spacing: { after: 200 }, indent: { left: 360 }, children: [new TextRun("6.4 System Settings")] }),

        new Paragraph({ spacing: { after: 100 }, children: [new TextRun({ text: "7. Troubleshooting", bold: true, size: 22 })] }),
        new Paragraph({ spacing: { after: 100 }, indent: { left: 360 }, children: [new TextRun("7.1 Common Issues")] }),
        new Paragraph({ spacing: { after: 100 }, indent: { left: 360 }, children: [new TextRun("7.2 Password Reset")] }),
        new Paragraph({ spacing: { after: 200 }, indent: { left: 360 }, children: [new TextRun("7.3 Contact Support")] }),

        new Paragraph({ children: [new PageBreak()] }),

        // === CHAPTER 1: GETTING STARTED ===
        new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("1. Getting Started")] }),
        new Paragraph({
          spacing: { after: 200 },
          children: [new TextRun({ text: "This chapter covers everything you need to know to start using the Hospital Health Management System (HMS).", size: 22 })]
        }),

        new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("1.1 System Requirements")] }),
        new Paragraph({
          spacing: { after: 200 },
          children: [new TextRun({ text: "Before accessing HMS, ensure your device meets the following requirements:", size: 22 })]
        }),
        new Table({
          width: { size: 9360, type: WidthType.DXA },
          columnWidths: [3120, 6240],
          rows: [
            new TableRow({
              children: [
                new TableCell({
                  borders, width: { size: 3120, type: WidthType.DXA }, margins: cellMargins,
                  shading: { fill: PRIMARY, type: ShadingType.CLEAR },
                  children: [new Paragraph({ children: [new TextRun({ text: "Component", bold: true, color: WHITE, size: 22 })] })]
                }),
                new TableCell({
                  borders, width: { size: 6240, type: WidthType.DXA }, margins: cellMargins,
                  shading: { fill: PRIMARY, type: ShadingType.CLEAR },
                  children: [new Paragraph({ children: [new TextRun({ text: "Requirement", bold: true, color: WHITE, size: 22 })] })]
                }),
              ]
            }),
            ...([
              ["Browser", "Chrome 90+, Firefox 88+, Safari 14+, Edge 90+"],
              ["Internet", "Stable broadband connection (minimum 5 Mbps)"],
              ["Screen Resolution", "1920x1080 recommended, minimum 1366x768"],
              ["Mobile", "iOS 14+ or Android 10+"],
              ["Software", "PDF reader for reports, Excel for data exports"],
            ].map((row, i) => new TableRow({
              children: [
                new TableCell({
                  borders, width: { size: 3120, type: WidthType.DXA }, margins: cellMargins,
                  shading: { fill: i % 2 === 0 ? LIGHT : WHITE, type: ShadingType.CLEAR },
                  children: [new Paragraph({ children: [new TextRun({ text: row[0], bold: true, size: 20 })] })]
                }),
                new TableCell({
                  borders, width: { size: 6240, type: WidthType.DXA }, margins: cellMargins,
                  shading: { fill: i % 2 === 0 ? LIGHT : WHITE, type: ShadingType.CLEAR },
                  children: [new Paragraph({ children: [new TextRun({ text: row[1], size: 20 })] })]
                }),
              ]
            })))
          ]
        }),

        new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("1.2 First-Time Login")] }),
        new Paragraph({
          spacing: { after: 100 },
          children: [new TextRun({ text: "Follow these steps to log in for the first time:", size: 22 })]
        }),
        new Paragraph({
          numbering: { reference: "steps", level: 0 },
          spacing: { after: 100 },
          children: [
            new TextRun({ text: "Open your web browser and navigate to ", size: 22 }),
            new TextRun({ text: "https://hms.yourhospital.com", bold: true, color: SECONDARY, size: 22 }),
          ]
        }),
        new Paragraph({
          numbering: { reference: "steps", level: 0 },
          spacing: { after: 100 },
          children: [new TextRun({ text: "Enter your username (email) and temporary password provided by your administrator", size: 22 })]
        }),
        new Paragraph({
          numbering: { reference: "steps", level: 0 },
          spacing: { after: 100 },
          children: [new TextRun({ text: "You will be prompted to change your password immediately", size: 22 })]
        }),
        new Paragraph({
          numbering: { reference: "steps", level: 0 },
          spacing: { after: 100 },
          children: [new TextRun({ text: "Set up Multi-Factor Authentication (MFA) when prompted", size: 22 })]
        }),
        new Paragraph({
          numbering: { reference: "steps", level: 0 },
          spacing: { after: 200 },
          children: [new TextRun({ text: "You will be directed to your personalized dashboard", size: 22 })]
        }),

        // Tip box
        new Table({
          width: { size: 9360, type: WidthType.DXA },
          columnWidths: [9360],
          rows: [
            new TableRow({
              children: [
                new TableCell({
                  borders: { top: { style: BorderStyle.SINGLE, size: 6, color: SUCCESS }, bottom: { style: BorderStyle.SINGLE, size: 6, color: SUCCESS }, left: { style: BorderStyle.SINGLE, size: 6, color: SUCCESS }, right: { style: BorderStyle.SINGLE, size: 6, color: SUCCESS } },
                  width: { size: 9360, type: WidthType.DXA },
                  margins: { top: 150, bottom: 150, left: 200, right: 200 },
                  shading: { fill: "EAFAF1", type: ShadingType.CLEAR },
                  children: [
                    new Paragraph({ spacing: { after: 100 }, children: [new TextRun({ text: "Tip:", bold: true, color: SUCCESS, size: 22 })] }),
                    new Paragraph({ children: [new TextRun({ text: "Your temporary password expires after 24 hours. If you cannot log in, contact your administrator for a new temporary password.", size: 20 })] })
                  ]
                })
              ]
            })
          ]
        }),

        new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("1.3 Setting Up MFA")] }),
        new Paragraph({
          spacing: { after: 100 },
          children: [new TextRun({ text: "Multi-Factor Authentication (MFA) is required for all users. HMS uses push notification as the primary MFA method:", size: 22 })]
        }),
        new Paragraph({
          numbering: { reference: "steps", level: 0 },
          spacing: { after: 100 },
          children: [new TextRun({ text: "Download the HMS Authenticator app from your device's app store", size: 22 })]
        }),
        new Paragraph({
          numbering: { reference: "steps", level: 0 },
          spacing: { after: 100 },
          children: [new TextRun({ text: "In the HMS web app, go to Settings > Security > MFA Setup", size: 22 })]
        }),
        new Paragraph({
          numbering: { reference: "steps", level: 0 },
          spacing: { after: 100 },
          children: [new TextRun({ text: "Scan the QR code displayed on screen with the authenticator app", size: 22 })]
        }),
        new Paragraph({
          numbering: { reference: "steps", level: 0 },
          spacing: { after: 100 },
          children: [new TextRun({ text: "Enter the 6-digit code from the app to verify setup", size: 22 })]
        }),
        new Paragraph({
          numbering: { reference: "steps", level: 0 },
          spacing: { after: 200 },
          children: [new TextRun({ text: "Save your backup codes in a secure location", size: 22 })]
        }),

        new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("1.4 Dashboard Overview")] }),
        new Paragraph({
          spacing: { after: 200 },
          children: [new TextRun({ text: "Your dashboard is your central hub for accessing all HMS features. The dashboard displays:", size: 22 })]
        }),
        new Paragraph({
          numbering: { reference: "bullets", level: 0 },
          spacing: { after: 100 },
          children: [
            new TextRun({ text: "Today's Appointments: ", bold: true, color: PRIMARY }),
            new TextRun("Quick view of all scheduled appointments for the day")
          ]
        }),
        new Paragraph({
          numbering: { reference: "bullets", level: 0 },
          spacing: { after: 100 },
          children: [
            new TextRun({ text: "Recent Patients: ", bold: true, color: PRIMARY }),
            new TextRun("Patients you've recently interacted with")
          ]
        }),
        new Paragraph({
          numbering: { reference: "bullets", level: 0 },
          spacing: { after: 100 },
          children: [
            new TextRun({ text: "Pending Tasks: ", bold: true, color: PRIMARY }),
            new TextRun("Lab results to review, prescriptions to sign, messages to respond to")
          ]
        }),
        new Paragraph({
          numbering: { reference: "bullets", level: 0 },
          spacing: { after: 100 },
          children: [
            new TextRun({ text: "Quick Actions: ", bold: true, color: PRIMARY }),
            new TextRun("Shortcuts to common tasks like creating appointments or searching patients")
          ]
        }),
        new Paragraph({
          numbering: { reference: "bullets", level: 0 },
          spacing: { after: 200 },
          children: [
            new TextRun({ text: "Notifications: ", bold: true, color: PRIMARY }),
            new TextRun("System alerts, messages, and security notifications")
          ]
        }),

        new Paragraph({ children: [new PageBreak()] }),

        // === CHAPTER 2: PATIENT MANAGEMENT ===
        new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("2. Patient Management")] }),
        new Paragraph({
          spacing: { after: 200 },
          children: [new TextRun({ text: "This chapter covers all patient-related operations in HMS.", size: 22 })]
        }),

        new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("2.1 Registering a New Patient")] }),
        new Paragraph({
          spacing: { after: 100 },
          children: [new TextRun({ text: "To register a new patient:", size: 22 })]
        }),
        new Paragraph({
          numbering: { reference: "steps", level: 0 },
          spacing: { after: 100 },
          children: [new TextRun({ text: "Navigate to Patients > Register New Patient from the main menu", size: 22 })]
        }),
        new Paragraph({
          numbering: { reference: "steps", level: 0 },
          spacing: { after: 100 },
          children: [new TextRun({ text: "Fill in the required fields: Full Name, Date of Birth, Gender, Contact Information", size: 22 })]
        }),
        new Paragraph({
          numbering: { reference: "steps", level: 0 },
          spacing: { after: 100 },
          children: [new TextRun({ text: "Enter insurance information if available", size: 22 })]
        }),
        new Paragraph({
          numbering: { reference: "steps", level: 0 },
          spacing: { after: 100 },
          children: [new TextRun({ text: "Add emergency contact details", size: 22 })]
        }),
        new Paragraph({
          numbering: { reference: "steps", level: 0 },
          spacing: { after: 200 },
          children: [new TextRun({ text: "Click 'Save' to create the patient record. The system will generate a unique Patient ID.", size: 22 })]
        }),

        new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("2.2 Searching for Patients")] }),
        new Paragraph({
          spacing: { after: 200 },
          children: [new TextRun({ text: "Use the global search bar at the top of any screen to find patients by name, ID, phone number, or email. Results appear as you type, and you can filter by department, date of birth, or insurance provider.", size: 22 })]
        }),

        new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("2.3 Viewing Patient Records")] }),
        new Paragraph({
          spacing: { after: 200 },
          children: [new TextRun({ text: "Click on any patient name to open their complete medical record. The patient profile includes tabs for Demographics, Medical History, Appointments, Prescriptions, Lab Results, and Billing. All information is updated in real-time across the system.", size: 22 })]
        }),

        new Paragraph({ children: [new PageBreak()] }),

        // === CHAPTER 3: APPOINTMENT SCHEDULING ===
        new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("3. Appointment Scheduling")] }),

        new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("3.1 Creating an Appointment")] }),
        new Paragraph({
          numbering: { reference: "steps", level: 0 },
          spacing: { after: 100 },
          children: [new TextRun({ text: "Navigate to Scheduling > New Appointment", size: 22 })]
        }),
        new Paragraph({
          numbering: { reference: "steps", level: 0 },
          spacing: { after: 100 },
          children: [new TextRun({ text: "Select the patient from the search field", size: 22 })]
        }),
        new Paragraph({
          numbering: { reference: "steps", level: 0 },
          spacing: { after: 100 },
          children: [new TextRun({ text: "Choose the provider (doctor) and appointment type", size: 22 })]
        }),
        new Paragraph({
          numbering: { reference: "steps", level: 0 },
          spacing: { after: 100 },
          children: [new TextRun({ text: "Select the date and time slot from available options", size: 22 })]
        }),
        new Paragraph({
          numbering: { reference: "steps", level: 0 },
          spacing: { after: 200 },
          children: [new TextRun({ text: "Click 'Confirm' to schedule. The patient will receive an automated confirmation via SMS/email.", size: 22 })]
        }),

        new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("3.2 Viewing the Calendar")] }),
        new Paragraph({
          spacing: { after: 200 },
          children: [new TextRun({ text: "The calendar view shows all appointments in daily, weekly, or monthly formats. Color codes indicate appointment status: Blue (confirmed), Yellow (pending), Green (completed), Red (cancelled). Use the filter options to view specific providers or departments.", size: 22 })]
        }),

        new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("3.3 Rescheduling Appointments")] }),
        new Paragraph({
          spacing: { after: 200 },
          children: [new TextRun({ text: "To reschedule, click on the appointment and select 'Reschedule'. Choose a new date/time from available slots. Both patient and provider will receive updated notifications. The system prevents double-booking automatically.", size: 22 })]
        }),

        new Paragraph({ children: [new PageBreak()] }),

        // === CHAPTER 4: ELECTRONIC HEALTH RECORDS ===
        new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("4. Electronic Health Records")] }),

        new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("4.1 Creating a New Encounter")] }),
        new Paragraph({
          spacing: { after: 200 },
          children: [new TextRun({ text: "When seeing a patient, click 'Start Encounter' from their profile. This creates a timestamped clinical session where you can record all interactions, notes, and orders for that visit.", size: 22 })]
        }),

        new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("4.2 Recording Vitals")] }),
        new Paragraph({
          spacing: { after: 200 },
          children: [new TextRun({ text: "Navigate to the Vitals tab within an encounter. Enter blood pressure, heart rate, temperature, respiratory rate, weight, and height. The system automatically calculates BMI and flags abnormal values in red.", size: 22 })]
        }),

        new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("4.3 Writing Clinical Notes")] }),
        new Paragraph({
          spacing: { after: 200 },
          children: [new TextRun({ text: "Use the SOAP (Subjective, Objective, Assessment, Plan) template or choose from specialty-specific templates. The auto-save feature preserves your work every 30 seconds. Templates can be customized and saved for reuse.", size: 22 })]
        }),

        new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("4.4 Managing Problem Lists")] }),
        new Paragraph({
          spacing: { after: 200 },
          children: [new TextRun({ text: "The Problem List tracks all active diagnoses. Add new problems with ICD-10 codes, mark problems as resolved or chronic, and track the timeline of each condition. This list is visible across all encounters for continuity of care.", size: 22 })]
        }),

        new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("4.5 Prescribing Medications")] }),
        new Paragraph({
          spacing: { after: 200 },
          children: [new TextRun({ text: "Go to the Prescriptions tab and click 'New Prescription'. Search for medications by name, select dosage, frequency, and duration. The system checks for drug interactions and allergies automatically. Prescriptions can be sent electronically to the pharmacy.", size: 22 })]
        }),

        new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("4.6 Ordering Lab Tests")] }),
        new Paragraph({
          spacing: { after: 200 },
          children: [new TextRun({ text: "Click 'Order Labs' within an encounter. Select from commonly ordered panels or search for specific tests. Add clinical notes for the lab. Results are delivered directly to the ordering provider's dashboard when ready.", size: 22 })]
        }),

        new Paragraph({ children: [new PageBreak()] }),

        // === CHAPTER 5: BILLING ===
        new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("5. Billing & Invoicing")] }),

        new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("5.1 Generating Invoices")] }),
        new Paragraph({
          spacing: { after: 200 },
          children: [new TextRun({ text: "Invoices are automatically generated when services are documented. Go to Billing > Pending Invoices to review. Verify charges, add any additional items, and click 'Generate Invoice'. The system calculates totals including taxes and insurance adjustments.", size: 22 })]
        }),

        new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("5.2 Processing Payments")] }),
        new Paragraph({
          spacing: { after: 200 },
          children: [new TextRun({ text: "Navigate to Billing > Payments. Select the invoice and choose payment method (cash, card, bank transfer, insurance). For cash payments, the system generates a receipt. For insurance, it creates a claim automatically.", size: 22 })]
        }),

        new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("5.3 Insurance Claims")] }),
        new Paragraph({
          spacing: { after: 200 },
          children: [new TextRun({ text: "The Claims section tracks all insurance submissions. Each claim shows status (Draft, Submitted, Under Review, Approved, Denied). Denied claims are flagged with reasons and can be corrected and resubmitted. The system maintains a 95% first-pass accuracy rate.", size: 22 })]
        }),

        new Paragraph({ children: [new PageBreak()] }),

        // === CHAPTER 6: ADMINISTRATION ===
        new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("6. Administration")] }),

        new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("6.1 Managing Users")] }),
        new Paragraph({
          spacing: { after: 200 },
          children: [new TextRun({ text: "Admins can add, edit, and deactivate user accounts from Administration > Users. When adding a new user, assign their role, department, and initial permissions. Deactivated accounts lose access immediately but audit logs are preserved.", size: 22 })]
        }),

        new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("6.2 Role-Based Access Control")] }),
        new Paragraph({
          spacing: { after: 200 },
          children: [new TextRun({ text: "HMS uses 15 predefined roles with hierarchical permissions. Admins can create custom roles with feature-level permissions. Role changes require Department Head approval and are fully audited. Temporary role elevation is supported for coverage situations.", size: 22 })]
        }),

        new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("6.3 Audit Logs")] }),
        new Paragraph({
          spacing: { after: 200 },
          children: [new TextRun({ text: "Access audit logs from Administration > Audit Logs. Every action is logged with who, what, when, where, why, and patient affected. Use filters to search by date range, user, action type, or patient. Export logs for compliance reporting.", size: 22 })]
        }),

        new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("6.4 System Settings")] }),
        new Paragraph({
          spacing: { after: 200 },
          children: [new TextRun({ text: "Configure system-wide settings from Administration > Settings. This includes email templates, notification preferences, appointment slot durations, department structures, and integration settings. Changes require admin approval and are version-controlled.", size: 22 })]
        }),

        new Paragraph({ children: [new PageBreak()] }),

        // === CHAPTER 7: TROUBLESHOOTING ===
        new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("7. Troubleshooting")] }),

        new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("7.1 Common Issues")] }),
        new Table({
          width: { size: 9360, type: WidthType.DXA },
          columnWidths: [3120, 6240],
          rows: [
            new TableRow({
              children: [
                new TableCell({
                  borders, width: { size: 3120, type: WidthType.DXA }, margins: cellMargins,
                  shading: { fill: PRIMARY, type: ShadingType.CLEAR },
                  children: [new Paragraph({ children: [new TextRun({ text: "Issue", bold: true, color: WHITE, size: 22 })] })]
                }),
                new TableCell({
                  borders, width: { size: 6240, type: WidthType.DXA }, margins: cellMargins,
                  shading: { fill: PRIMARY, type: ShadingType.CLEAR },
                  children: [new Paragraph({ children: [new TextRun({ text: "Solution", bold: true, color: WHITE, size: 22 })] })]
                }),
              ]
            }),
            ...([
              ["Cannot log in", "Check username/password. Ensure MFA is set up. Clear browser cache."],
              ["Page loads slowly", "Check internet connection. Try a different browser. Disable browser extensions."],
              ["Data not saving", "Check for error messages. Ensure all required fields are filled. Try refreshing."],
              ["Cannot find patient", "Try different search terms. Check spelling. Use filters to narrow results."],
              ["Appointment not showing", "Refresh the calendar. Check the correct date/provider is selected."],
            ].map((row, i) => new TableRow({
              children: [
                new TableCell({
                  borders, width: { size: 3120, type: WidthType.DXA }, margins: cellMargins,
                  shading: { fill: i % 2 === 0 ? LIGHT : WHITE, type: ShadingType.CLEAR },
                  children: [new Paragraph({ children: [new TextRun({ text: row[0], bold: true, size: 20 })] })]
                }),
                new TableCell({
                  borders, width: { size: 6240, type: WidthType.DXA }, margins: cellMargins,
                  shading: { fill: i % 2 === 0 ? LIGHT : WHITE, type: ShadingType.CLEAR },
                  children: [new Paragraph({ children: [new TextRun({ text: row[1], size: 20 })] })]
                }),
              ]
            })))
          ]
        }),

        new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("7.2 Password Reset")] }),
        new Paragraph({
          spacing: { after: 200 },
          children: [new TextRun({ text: "Click 'Forgot Password' on the login page to receive a reset link via email. The link expires after 15 minutes. If you cannot access your email, contact your administrator for a password reset. After resetting, you will need to log in again on all devices.", size: 22 })]
        }),

        new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("7.3 Contact Support")] }),
        new Paragraph({
          spacing: { after: 200 },
          children: [new TextRun({ text: "For technical support, contact your internal IT helpdesk or email support@dkeemz.com. Include your username, a description of the issue, and any error messages. For urgent issues affecting patient care, call the 24/7 support hotline.", size: 22 })]
        }),

        // Warning box
        new Table({
          width: { size: 9360, type: WidthType.DXA },
          columnWidths: [9360],
          rows: [
            new TableRow({
              children: [
                new TableCell({
                  borders: { top: { style: BorderStyle.SINGLE, size: 6, color: WARNING }, bottom: { style: BorderStyle.SINGLE, size: 6, color: WARNING }, left: { style: BorderStyle.SINGLE, size: 6, color: WARNING }, right: { style: BorderStyle.SINGLE, size: 6, color: WARNING } },
                  width: { size: 9360, type: WidthType.DXA },
                  margins: { top: 150, bottom: 150, left: 200, right: 200 },
                  shading: { fill: "FEF9E7", type: ShadingType.CLEAR },
                  children: [
                    new Paragraph({ spacing: { after: 100 }, children: [new TextRun({ text: "Important:", bold: true, color: WARNING, size: 22 })] }),
                    new Paragraph({ children: [new TextRun({ text: "Never share your login credentials. Always lock your screen when stepping away (Windows: Win+L, Mac: Cmd+Ctrl+Q). Report any suspicious activity immediately to your administrator.", size: 20 })] })
                  ]
                })
              ]
            })
          ]
        }),

        new Paragraph({ spacing: { before: 600 }, children: [] }),
        new Paragraph({
          alignment: AlignmentType.CENTER,
          border: { top: { style: BorderStyle.SINGLE, size: 6, color: SECONDARY, space: 1 } },
          children: [new TextRun({ text: " ", size: 12 })]
        }),
        new Paragraph({
          alignment: AlignmentType.CENTER,
          children: [new TextRun({ text: "End of User Guide", italic: true, size: 22, color: "5D6D7E" })]
        }),
        new Paragraph({
          alignment: AlignmentType.CENTER,
          children: [new TextRun({ text: "For additional help, contact support@dkeemz.com", size: 20, color: "ABB2B9" })]
        }),
      ]
    },
  ]
});

Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync("C:/Users/ABDUL/Desktop/Projects/HMS/HMS_User_Guide.docx", buffer);
  console.log("User Guide created successfully!");
});
