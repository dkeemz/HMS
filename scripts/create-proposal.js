const fs = require('fs');
const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
        Header, Footer, AlignmentType, HeadingLevel, BorderStyle, WidthType,
        ShadingType, PageNumber, PageBreak, LevelFormat, TabStopType, TabStopPosition,
        ExternalHyperlink } = require('docx');

// Color scheme - Professional healthcare blue
const PRIMARY = "1B4F72";
const SECONDARY = "2E86C1";
const ACCENT = "85C1E9";
const DARK = "1A1A1A";
const LIGHT = "EBF5FB";
const WHITE = "FFFFFF";

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
      { reference: "checklist",
        levels: [{ level: 0, format: LevelFormat.BULLET, text: "\u2713", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
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
          children: [new TextRun({ text: "A Unified Platform for Modern Healthcare", size: 28, italic: true, color: SECONDARY })]
        }),
        new Paragraph({
          alignment: AlignmentType.CENTER,
          spacing: { after: 100 },
          children: [new TextRun({ text: "Replacing Fragmented Tools with One Intelligent System", size: 24, color: "5D6D7E" })]
        }),
        new Paragraph({ spacing: { before: 2000 }, children: [] }),
        new Paragraph({
          alignment: AlignmentType.CENTER,
          spacing: { after: 100 },
          children: [new TextRun({ text: "Prepared for:", size: 22, color: "5D6D7E" })]
        }),
        new Paragraph({
          alignment: AlignmentType.CENTER,
          spacing: { after: 100 },
          children: [new TextRun({ text: "[Hospital Name]", size: 32, bold: true, color: PRIMARY })]
        }),
        new Paragraph({
          alignment: AlignmentType.CENTER,
          spacing: { after: 100 },
          children: [new TextRun({ text: "By: DKEEMZ Technologies", size: 22, color: "5D6D7E" })]
        }),
        new Paragraph({
          alignment: AlignmentType.CENTER,
          spacing: { after: 100 },
          children: [new TextRun({ text: "Date: July 2026", size: 22, color: "5D6D7E" })]
        }),
        new Paragraph({
          alignment: AlignmentType.CENTER,
          children: [new TextRun({ text: "Version 1.0", size: 20, color: "ABB2B9" })]
        }),
      ]
    },

    // === EXECUTIVE SUMMARY ===
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
              new TextRun({ text: "HMS Proposal", font: "Arial", size: 18, color: "5D6D7E" }),
              new TextRun({ text: "\t", children: [] }),
              new TextRun({ text: "Confidential", font: "Arial", size: 18, color: "5D6D7E", italics: true }),
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
        new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("Executive Summary")] }),
        new Paragraph({
          spacing: { after: 200 },
          children: [new TextRun({ text: "The healthcare industry faces an unprecedented challenge: fragmented systems that force doctors to navigate multiple tools for a single patient encounter. Studies show physicians spend ", size: 22 }),
          new TextRun({ text: "49% of their workday", size: 22, bold: true, color: PRIMARY }),
          new TextRun({ text: " on electronic health records and administrative tasks, with only ", size: 22 }),
          new TextRun({ text: "27% on direct patient care", size: 22, bold: true, color: PRIMARY }),
          new TextRun({ text: ". This inefficiency costs the average hospital ", size: 22 }),
          new TextRun({ text: "$2.4 million annually", size: 22, bold: true, color: PRIMARY }),
          new TextRun({ text: " in lost productivity.", size: 22 })]
        }),
        new Paragraph({
          spacing: { after: 200 },
          children: [new TextRun({ text: "The Hospital Health Management System (HMS) is a unified platform that consolidates all hospital operations into one intelligent system. From patient registration to billing, appointment scheduling to electronic health records, HMS eliminates the need for multiple disconnected tools.", size: 22 })]
        }),

        // Key Benefits Table
        new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("Why HMS?")] }),
        new Table({
          width: { size: 9360, type: WidthType.DXA },
          columnWidths: [3120, 3120, 3120],
          rows: [
            new TableRow({
              children: [
                new TableCell({
                  borders, width: { size: 3120, type: WidthType.DXA }, margins: cellMargins,
                  shading: { fill: PRIMARY, type: ShadingType.CLEAR },
                  children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "Current State", bold: true, color: WHITE, size: 22 })] })]
                }),
                new TableCell({
                  borders, width: { size: 3120, type: WidthType.DXA }, margins: cellMargins,
                  shading: { fill: PRIMARY, type: ShadingType.CLEAR },
                  children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "With HMS", bold: true, color: WHITE, size: 22 })] })]
                }),
                new TableCell({
                  borders, width: { size: 3120, type: WidthType.DXA }, margins: cellMargins,
                  shading: { fill: PRIMARY, type: ShadingType.CLEAR },
                  children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "Impact", bold: true, color: WHITE, size: 22 })] })]
                }),
              ]
            }),
            ...([
              ["5-8 different tools", "One unified platform", "60% less context switching"],
              ["Paper-based handoffs", "Digital care coordination", "40% fewer errors"],
              ["30+ min documentation", "5-min smart templates", "85% faster charting"],
              ["Manual billing errors", "Automated claims processing", "95% first-pass accuracy"],
              ["Reactive scheduling", "AI-optimized scheduling", "35% more efficient"],
            ].map((row, i) => new TableRow({
              children: row.map(cell => new TableCell({
                borders, width: { size: 3120, type: WidthType.DXA }, margins: cellMargins,
                shading: { fill: i % 2 === 0 ? LIGHT : WHITE, type: ShadingType.CLEAR },
                children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: cell, size: 20 })] })]
              }))
            })))
          ]
        }),

        new Paragraph({ children: [new PageBreak()] }),

        // === THE PROBLEM ===
        new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("The Problem We Solve")] }),
        new Paragraph({
          spacing: { after: 200 },
          children: [new TextRun({ text: "Today's hospitals operate in a state of digital chaos. Critical patient information is scattered across disconnected systems, paper charts, and tribal knowledge. This fragmentation creates:", size: 22 })]
        }),
        new Paragraph({
          numbering: { reference: "bullets", level: 0 },
          spacing: { after: 100 },
          children: [
            new TextRun({ text: "Physician Burnout: ", bold: true, color: PRIMARY }),
            new TextRun("Doctors spend more time fighting software than treating patients")
          ]
        }),
        new Paragraph({
          numbering: { reference: "bullets", level: 0 },
          spacing: { after: 100 },
          children: [
            new TextRun({ text: "Patient Safety Risks: ", bold: true, color: PRIMARY }),
            new TextRun("Incomplete records lead to medical errors, the third leading cause of death in the US")
          ]
        }),
        new Paragraph({
          numbering: { reference: "bullets", level: 0 },
          spacing: { after: 100 },
          children: [
            new TextRun({ text: "Revenue Leakage: ", bold: true, color: PRIMARY }),
            new TextRun("Manual billing processes result in 15-20% claim denial rates")
          ]
        }),
        new Paragraph({
          numbering: { reference: "bullets", level: 0 },
          spacing: { after: 100 },
          children: [
            new TextRun({ text: "Compliance Vulnerability: ", bold: true, color: PRIMARY }),
            new TextRun("Disparate systems make HIPAA compliance nearly impossible to maintain")
          ]
        }),
        new Paragraph({
          numbering: { reference: "bullets", level: 0 },
          spacing: { after: 200 },
          children: [
            new TextRun({ text: "Patient Dissatisfaction: ", bold: true, color: PRIMARY }),
            new TextRun("Long wait times, repeated paperwork, and poor care coordination frustrate patients")
          ]
        }),

        // === THE SOLUTION ===
        new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("Our Solution")] }),
        new Paragraph({
          spacing: { after: 200 },
          children: [new TextRun({ text: "HMS is not just another EHR. It is a comprehensive hospital operating system that unifies every aspect of healthcare delivery into a single, intelligent platform.", size: 22, bold: true })]
        }),

        new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("Core Capabilities")] }),

        // Feature cards as table
        new Table({
          width: { size: 9360, type: WidthType.DXA },
          columnWidths: [4680, 4680],
          rows: [
            new TableRow({
              children: [
                new TableCell({
                  borders, width: { size: 4680, type: WidthType.DXA }, margins: cellMargins,
                  shading: { fill: LIGHT, type: ShadingType.CLEAR },
                  children: [
                    new Paragraph({ spacing: { after: 80 }, children: [new TextRun({ text: "Unified Patient Records", bold: true, size: 22, color: PRIMARY })] }),
                    new Paragraph({ children: [new TextRun({ text: "Complete medical history accessible from any device. Real-time updates across all departments. FHIR-compatible for interoperability.", size: 20 })] })
                  ]
                }),
                new TableCell({
                  borders, width: { size: 4680, type: WidthType.DXA }, margins: cellMargins,
                  shading: { fill: LIGHT, type: ShadingType.CLEAR },
                  children: [
                    new Paragraph({ spacing: { after: 80 }, children: [new TextRun({ text: "Smart Scheduling", bold: true, size: 22, color: PRIMARY })] }),
                    new Paragraph({ children: [new TextRun({ text: "AI-powered appointment optimization. Automated conflict resolution. Multi-provider coordination with real-time availability.", size: 20 })] })
                  ]
                }),
              ]
            }),
            new TableRow({
              children: [
                new TableCell({
                  borders, width: { size: 4680, type: WidthType.DXA }, margins: cellMargins,
                  shading: { fill: WHITE, type: ShadingType.CLEAR },
                  children: [
                    new Paragraph({ spacing: { after: 80 }, children: [new TextRun({ text: "Integrated Billing", bold: true, size: 22, color: PRIMARY })] }),
                    new Paragraph({ children: [new TextRun({ text: "Automated charge capture. Real-time insurance verification. Claims processing with 95% first-pass accuracy.", size: 20 })] })
                  ]
                }),
                new TableCell({
                  borders, width: { size: 4680, type: WidthType.DXA }, margins: cellMargins,
                  shading: { fill: WHITE, type: ShadingType.CLEAR },
                  children: [
                    new Paragraph({ spacing: { after: 80 }, children: [new TextRun({ text: "Clinical Decision Support", bold: true, size: 22, color: PRIMARY })] }),
                    new Paragraph({ children: [new TextRun({ text: "Evidence-based alerts. Drug interaction checks. Automated care pathways and clinical protocols.", size: 20 })] })
                  ]
                }),
              ]
            }),
            new TableRow({
              children: [
                new TableCell({
                  borders, width: { size: 4680, type: WidthType.DXA }, margins: cellMargins,
                  shading: { fill: LIGHT, type: ShadingType.CLEAR },
                  children: [
                    new Paragraph({ spacing: { after: 80 }, children: [new TextRun({ text: "Patient Portal", bold: true, size: 22, color: PRIMARY })] }),
                    new Paragraph({ children: [new TextRun({ text: "Self-service appointment booking. Secure messaging with providers. Access to test results and medical records.", size: 20 })] })
                  ]
                }),
                new TableCell({
                  borders, width: { size: 4680, type: WidthType.DXA }, margins: cellMargins,
                  shading: { fill: LIGHT, type: ShadingType.CLEAR },
                  children: [
                    new Paragraph({ spacing: { after: 80 }, children: [new TextRun({ text: "Analytics & Reporting", bold: true, size: 22, color: PRIMARY })] }),
                    new Paragraph({ children: [new TextRun({ text: "Real-time dashboards. Operational insights. Compliance reporting. Population health management.", size: 20 })] })
                  ]
                }),
              ]
            }),
          ]
        }),

        new Paragraph({ children: [new PageBreak()] }),

        // === TECHNICAL ARCHITECTURE ===
        new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("Technical Architecture")] }),
        new Paragraph({
          spacing: { after: 200 },
          children: [new TextRun({ text: "HMS is built on a modern, scalable architecture designed for healthcare's unique demands:", size: 22 })]
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
                  children: [new Paragraph({ children: [new TextRun({ text: "Technology", bold: true, color: WHITE, size: 22 })] })]
                }),
              ]
            }),
            ...([
              ["Frontend", "React 19 + Next.js 15 (Web), React Native (Mobile)"],
              ["Backend", "NestJS 11 with TypeScript, modular monolith architecture"],
              ["Database", "PostgreSQL 17 with row-level security and encryption at rest"],
              ["Authentication", "Keycloak 26.x with MFA, SSO, and HIPAA-compliant audit trails"],
              ["Interoperability", "HAPI FHIR 8.x for HL7/FHIR compliance"],
              ["Deployment", "Hybrid cloud (on-premise + AWS/Azure) with Docker & Kubernetes"],
              ["Security", "AES-256 encryption, TLS 1.3, role-based access control, break-glass protocols"],
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

        // === COMPLIANCE ===
        new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("Compliance & Security")] }),
        new Paragraph({
          spacing: { after: 200 },
          children: [new TextRun({ text: "HMS is designed from the ground up to meet the strictest healthcare compliance requirements:", size: 22 })]
        }),
        new Paragraph({
          numbering: { reference: "checklist", level: 0 },
          spacing: { after: 100 },
          children: [
            new TextRun({ text: "HIPAA Compliance: ", bold: true }),
            new TextRun("Full technical safeguards including encryption, audit trails, access controls, and automatic session termination")
          ]
        }),
        new Paragraph({
          numbering: { reference: "checklist", level: 0 },
          spacing: { after: 100 },
          children: [
            new TextRun({ text: "NDPA (Nigeria): ", bold: true }),
            new TextRun("Nigerian Data Protection Act 2023 compliance with data localization options")
          ]
        }),
        new Paragraph({
          numbering: { reference: "checklist", level: 0 },
          spacing: { after: 100 },
          children: [
            new TextRun({ text: "PDPA: ", bold: true }),
            new TextRun("Personal Data Protection Act compliance for multi-jurisdictional operations")
          ]
        }),
        new Paragraph({
          numbering: { reference: "checklist", level: 0 },
          spacing: { after: 100 },
          children: [
            new TextRun({ text: "NAFDAC: ", bold: true }),
            new TextRun("Pharmaceutical tracking and compliance for drug management modules")
          ]
        }),
        new Paragraph({
          numbering: { reference: "checklist", level: 0 },
          spacing: { after: 200 },
          children: [
            new TextRun({ text: "Cybercrimes Act 2015: ", bold: true }),
            new TextRun("Full compliance with Nigerian cybersecurity legislation")
          ]
        }),

        new Paragraph({ children: [new PageBreak()] }),

        // === IMPLEMENTATION ===
        new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("Implementation Roadmap")] }),
        new Paragraph({
          spacing: { after: 200 },
          children: [new TextRun({ text: "Our proven 8-phase implementation approach ensures minimal disruption to your operations:", size: 22 })]
        }),
        new Table({
          width: { size: 9360, type: WidthType.DXA },
          columnWidths: [780, 3120, 3120, 2340],
          rows: [
            new TableRow({
              children: [
                new TableCell({
                  borders, width: { size: 780, type: WidthType.DXA }, margins: cellMargins,
                  shading: { fill: PRIMARY, type: ShadingType.CLEAR },
                  children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "#", bold: true, color: WHITE, size: 20 })] })]
                }),
                new TableCell({
                  borders, width: { size: 3120, type: WidthType.DXA }, margins: cellMargins,
                  shading: { fill: PRIMARY, type: ShadingType.CLEAR },
                  children: [new Paragraph({ children: [new TextRun({ text: "Phase", bold: true, color: WHITE, size: 20 })] })]
                }),
                new TableCell({
                  borders, width: { size: 3120, type: WidthType.DXA }, margins: cellMargins,
                  shading: { fill: PRIMARY, type: ShadingType.CLEAR },
                  children: [new Paragraph({ children: [new TextRun({ text: "Deliverables", bold: true, color: WHITE, size: 20 })] })]
                }),
                new TableCell({
                  borders, width: { size: 2340, type: WidthType.DXA }, margins: cellMargins,
                  shading: { fill: PRIMARY, type: ShadingType.CLEAR },
                  children: [new Paragraph({ children: [new TextRun({ text: "Duration", bold: true, color: WHITE, size: 20 })] })]
                }),
              ]
            }),
            ...([
              ["1", "Foundation & Authentication", "User management, RBAC, MFA, audit logging", "4 weeks"],
              ["2", "Patient Management", "Registration, profiles, medical history", "3 weeks"],
              ["3", "Doctor & Department Mgmt", "Provider directories, department structure", "2 weeks"],
              ["4", "Scheduling Core", "Appointments, shifts, calendar integration", "4 weeks"],
              ["5", "EHR Documentation", "Clinical notes, templates, vitals", "4 weeks"],
              ["6", "EHR Clinical Lists", "Problem lists, medications, allergies", "2 weeks"],
              ["7", "Billing Foundation", "Charge capture, invoicing, payments", "3 weeks"],
              ["8", "Billing & Revenue", "Insurance claims, reporting, analytics", "3 weeks"],
            ].map((row, i) => new TableRow({
              children: [
                new TableCell({
                  borders, width: { size: 780, type: WidthType.DXA }, margins: cellMargins,
                  shading: { fill: i % 2 === 0 ? LIGHT : WHITE, type: ShadingType.CLEAR },
                  children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: row[0], bold: true, size: 20 })] })]
                }),
                new TableCell({
                  borders, width: { size: 3120, type: WidthType.DXA }, margins: cellMargins,
                  shading: { fill: i % 2 === 0 ? LIGHT : WHITE, type: ShadingType.CLEAR },
                  children: [new Paragraph({ children: [new TextRun({ text: row[1], size: 20 })] })]
                }),
                new TableCell({
                  borders, width: { size: 3120, type: WidthType.DXA }, margins: cellMargins,
                  shading: { fill: i % 2 === 0 ? LIGHT : WHITE, type: ShadingType.CLEAR },
                  children: [new Paragraph({ children: [new TextRun({ text: row[2], size: 20 })] })]
                }),
                new TableCell({
                  borders, width: { size: 2340, type: WidthType.DXA }, margins: cellMargins,
                  shading: { fill: i % 2 === 0 ? LIGHT : WHITE, type: ShadingType.CLEAR },
                  children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: row[3], size: 20 })] })]
                }),
              ]
            })))
          ]
        }),

        // === ROI ===
        new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("Return on Investment")] }),
        new Paragraph({
          spacing: { after: 200 },
          children: [new TextRun({ text: "Based on industry benchmarks and comparable implementations:", size: 22 })]
        }),
        new Table({
          width: { size: 9360, type: WidthType.DXA },
          columnWidths: [4680, 4680],
          rows: [
            new TableRow({
              children: [
                new TableCell({
                  borders, width: { size: 4680, type: WidthType.DXA }, margins: cellMargins,
                  shading: { fill: PRIMARY, type: ShadingType.CLEAR },
                  children: [new Paragraph({ children: [new TextRun({ text: "Metric", bold: true, color: WHITE, size: 22 })] })]
                }),
                new TableCell({
                  borders, width: { size: 4680, type: WidthType.DXA }, margins: cellMargins,
                  shading: { fill: PRIMARY, type: ShadingType.CLEAR },
                  children: [new Paragraph({ children: [new TextRun({ text: "Expected Improvement", bold: true, color: WHITE, size: 22 })] })]
                }),
              ]
            }),
            ...([
              ["Physician Documentation Time", "60-70% reduction"],
              ["Claim Denial Rate", "85% reduction (from 15% to <2%)"],
              ["Patient Wait Times", "40% reduction"],
              ["Staff Productivity", "35% improvement"],
              ["Patient Satisfaction (HCAHPS)", "25% improvement"],
              ["Annual Cost Savings", "$1.8-2.4 million"],
              ["ROI Timeline", "12-18 months"],
            ].map((row, i) => new TableRow({
              children: [
                new TableCell({
                  borders, width: { size: 4680, type: WidthType.DXA }, margins: cellMargins,
                  shading: { fill: i % 2 === 0 ? LIGHT : WHITE, type: ShadingType.CLEAR },
                  children: [new Paragraph({ children: [new TextRun({ text: row[0], size: 20 })] })]
                }),
                new TableCell({
                  borders, width: { size: 4680, type: WidthType.DXA }, margins: cellMargins,
                  shading: { fill: i % 2 === 0 ? LIGHT : WHITE, type: ShadingType.CLEAR },
                  children: [new Paragraph({ children: [new TextRun({ text: row[1], bold: true, size: 20, color: PRIMARY })] })]
                }),
              ]
            })))
          ]
        }),

        new Paragraph({ children: [new PageBreak()] }),

        // === WHY CHOOSE US ===
        new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("Why Choose DKEEMZ Technologies?")] }),
        new Paragraph({
          spacing: { after: 200 },
          children: [new TextRun({ text: "We are not just developers. We are healthcare technology specialists who understand the unique challenges of modern hospitals.", size: 22 })]
        }),
        new Paragraph({
          numbering: { reference: "bullets", level: 0 },
          spacing: { after: 100 },
          children: [
            new TextRun({ text: "Healthcare Expertise: ", bold: true, color: PRIMARY }),
            new TextRun("Deep understanding of clinical workflows and compliance requirements")
          ]
        }),
        new Paragraph({
          numbering: { reference: "bullets", level: 0 },
          spacing: { after: 100 },
          children: [
            new TextRun({ text: "Modern Technology Stack: ", bold: true, color: PRIMARY }),
            new TextRun("Built on enterprise-grade, future-proof technology")
          ]
        }),
        new Paragraph({
          numbering: { reference: "bullets", level: 0 },
          spacing: { after: 100 },
          children: [
            new TextRun({ text: "Proven Methodology: ", bold: true, color: PRIMARY }),
            new TextRun("8-phase implementation with continuous delivery and feedback loops")
          ]
        }),
        new Paragraph({
          numbering: { reference: "bullets", level: 0 },
          spacing: { after: 100 },
          children: [
            new TextRun({ text: "Local Compliance: ", bold: true, color: PRIMARY }),
            new TextRun("Full compliance with Nigerian and international healthcare regulations")
          ]
        }),
        new Paragraph({
          numbering: { reference: "bullets", level: 0 },
          spacing: { after: 200 },
          children: [
            new TextRun({ text: "Ongoing Support: ", bold: true, color: PRIMARY }),
            new TextRun("24/7 support with guaranteed SLAs and dedicated account management")
          ]
        }),

        // === NEXT STEPS ===
        new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("Next Steps")] }),
        new Paragraph({
          spacing: { after: 100 },
          children: [new TextRun({ text: "We propose the following path forward:", size: 22 })]
        }),
        new Paragraph({
          numbering: { reference: "numbers", level: 0 },
          spacing: { after: 100 },
          children: [
            new TextRun({ text: "Discovery Workshop: ", bold: true }),
            new TextRun("2-day on-site session to map your current workflows and identify optimization opportunities")
          ]
        }),
        new Paragraph({
          numbering: { reference: "numbers", level: 0 },
          spacing: { after: 100 },
          children: [
            new TextRun({ text: "Proof of Concept: ", bold: true }),
            new TextRun("4-week pilot with one department to demonstrate value and gather feedback")
          ]
        }),
        new Paragraph({
          numbering: { reference: "numbers", level: 0 },
          spacing: { after: 100 },
          children: [
            new TextRun({ text: "Full Implementation: ", bold: true }),
            new TextRun("25-week phased rollout across all departments")
          ]
        }),
        new Paragraph({
          numbering: { reference: "numbers", level: 0 },
          spacing: { after: 200 },
          children: [
            new TextRun({ text: "Go-Live & Optimization: ", bold: true }),
            new TextRun("Continuous improvement based on data-driven insights")
          ]
        }),

        // === CONTACT ===
        new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("Contact Us")] }),
        new Table({
          width: { size: 9360, type: WidthType.DXA },
          columnWidths: [3120, 6240],
          rows: [
            ...([
              ["Company", "DKEEMZ Technologies"],
              ["Email", "abdulhakeem.abg@gmail.com"],
              ["GitHub", "github.com/dkeemz/HMS"],
              ["Phone", "[Your Phone Number]"],
              ["Address", "[Your Address]"],
            ].map((row, i) => new TableRow({
              children: [
                new TableCell({
                  borders, width: { size: 3120, type: WidthType.DXA }, margins: cellMargins,
                  shading: { fill: LIGHT, type: ShadingType.CLEAR },
                  children: [new Paragraph({ children: [new TextRun({ text: row[0], bold: true, size: 20 })] })]
                }),
                new TableCell({
                  borders, width: { size: 6240, type: WidthType.DXA }, margins: cellMargins,
                  shading: { fill: LIGHT, type: ShadingType.CLEAR },
                  children: [new Paragraph({ children: [new TextRun({ text: row[1], size: 20 })] })]
                }),
              ]
            })))
          ]
        }),

        new Paragraph({ spacing: { before: 600 }, children: [] }),
        new Paragraph({
          alignment: AlignmentType.CENTER,
          spacing: { after: 200 },
          border: { top: { style: BorderStyle.SINGLE, size: 6, color: SECONDARY, space: 1 } },
          children: [new TextRun({ text: " ", size: 12 })]
        }),
        new Paragraph({
          alignment: AlignmentType.CENTER,
          children: [new TextRun({ text: "Thank you for considering DKEEMZ Technologies as your technology partner.", italic: true, size: 22, color: "5D6D7E" })]
        }),
        new Paragraph({
          alignment: AlignmentType.CENTER,
          spacing: { after: 200 },
          children: [new TextRun({ text: "We look forward to transforming your healthcare delivery.", italic: true, size: 22, color: "5D6D7E" })]
        }),
      ]
    },
  ]
});

Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync("C:/Users/ABDUL/Desktop/Projects/HMS/HMS_Proposal.docx", buffer);
  console.log("Proposal created successfully!");
});
