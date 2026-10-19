/**
 * =========================================================================
 *         EXECUTIVE LEAD DIRECTORY — GOOGLE SHEETS LIVE ENGINE v2.5
 *                     Engineered by Al Hossain Rifat
 * =========================================================================
 * Features:
 *   1. Auto-Creates a Standalone Google Sheet for each lead search session.
 *   2. Single-Row Master Bar (Row 1): Topic name on left + 4 Live KPI Badges
 *      (Total Leads, Emails Found, Phones Verified, Top Rated) in Google Maps Brand Colors!
 *   3. Row 2: Sticky Frozen Header with user-specified hierarchy:
 *      # | Business Name | Email Address | Phone Number | Website | Category |
 *      Rating & Reviews | Social Profiles | Google Maps | Full Address | Quality Score
 *   4. Strict Text Clipping: WrapStrategy.CLIP prevents text bleeding out of cells.
 *   5. Clean Embedded Hyperlinks: "📍 Map Link" and "🌐 Website".
 *   6. Real-time live row streaming + final quality hierarchy overwrite.
 * =========================================================================
 */

function doGet(e) {
  return ContentService.createTextOutput(JSON.stringify({
    status: "online",
    message: "Google Maps Lead Harvester Google Sheets Webhook is active and listening!"
  })).setMimeType(ContentService.MimeType.JSON);
}

function doPost(e) {
  try {
    const data = JSON.parse(e.postData.contents);
    const action = data.action || "sync";
    const topic = data.topic ? data.topic.trim() : "Business Leads";
    let sheetId = data.sheet_id || null;
    let ss;

    // 1. Target or create the spreadsheet
    if (!sheetId) {
      let nowStr = "";
      try {
        nowStr = Utilities.formatDate(new Date(), Session.getScriptTimeZone() || "GMT", "yyyy-MM-dd HH:mm");
      } catch (err) {
        nowStr = new Date().toISOString().substring(0, 16).replace("T", " ");
      }
      const title = topic.toUpperCase() + " — Lead Directory (" + nowStr + ")";
      ss = SpreadsheetApp.create(title);
      sheetId = ss.getId();
      const sheet = ss.getActiveSheet();
      setupSheetLayout(sheet, topic);
    } else {
      try {
        ss = SpreadsheetApp.openById(sheetId);
      } catch (openErr) {
        const title = topic.toUpperCase() + " — Lead Directory";
        ss = SpreadsheetApp.create(title);
        sheetId = ss.getId();
        const sheet = ss.getActiveSheet();
        setupSheetLayout(sheet, topic);
      }
    }

    const sheet = ss.getActiveSheet();

    // 2. Batch sync or live row appending
    const rows = data.rows || [];
    const mode = data.mode || "append";
    let startRow = 3;

    if (mode === "replace") {
      const lastRow = sheet.getLastRow();
      if (lastRow >= 3) {
        sheet.getRange(3, 1, lastRow - 2, 11).clearContent();
      }
      startRow = 3;
    } else {
      startRow = Math.max(3, sheet.getLastRow() + 1);
    }

    const newValues = [];
    for (let i = 0; i < rows.length; i++) {
      const r = rows[i];

      // Format Website hyperlink or NOT FOUND
      let webCell = "NOT FOUND";
      if (r.website && r.website !== "N/A" && r.website !== "NOT FOUND" && r.website.startsWith("http")) {
        let domain = "";
        try {
          domain = r.website.replace(/^https?:\/\//i, "").replace(/^www\./i, "").split("/")[0];
        } catch (ex) {
          domain = "Visit Site";
        }
        webCell = '=HYPERLINK("' + r.website + '", "🌐 ' + (domain || "Visit Site") + '")';
      } else if (r.website && r.website !== "N/A" && r.website !== "NOT FOUND") {
        webCell = r.website;
      }

      // Format Google Maps hyperlink or NOT FOUND
      let mapsCell = "NOT FOUND";
      if (r.maps_url && r.maps_url !== "N/A" && r.maps_url !== "NOT FOUND" && r.maps_url.startsWith("http")) {
        mapsCell = '=HYPERLINK("' + r.maps_url + '", "📍 Map Link")';
      } else if (r.maps_url && r.maps_url !== "N/A") {
        mapsCell = r.maps_url;
      }

      // Merged Rating & Reviews or NOT FOUND
      let ratingCell = "NOT FOUND";
      if (r.rating_reviews && r.rating_reviews !== "-" && r.rating_reviews !== "NOT FOUND") {
        ratingCell = r.rating_reviews;
      } else if (r.rating && r.rating > 0) {
        ratingCell = "⭐ " + r.rating + (r.reviews ? " (" + r.reviews + ")" : "");
      }

      const emailVal = (r.email && r.email !== "N/A" && r.email !== "NOT FOUND") ? r.email : "NOT FOUND";
      const phoneVal = (r.phone && r.phone !== "N/A" && r.phone !== "NOT FOUND") ? r.phone : "NOT FOUND";
      const socialsVal = (r.social_profiles && r.social_profiles !== "N/A" && r.social_profiles !== "NOT FOUND") ? r.social_profiles : "NOT FOUND";
      const addressVal = (r.address && r.address !== "N/A" && r.address !== "NOT FOUND") ? r.address : "NOT FOUND";

      // Column Hierarchy requested:
      // 1: # | 2: Name | 3: Email | 4: Phone | 5: Website | 6: Category |
      // 7: Rating & Reviews | 8: Social Profiles | 9: Google Maps | 10: Address | 11: Quality Score
      newValues.push([
        r.rank !== undefined ? r.rank : (startRow - 2 + i),
        r.business_name || "NOT FOUND",
        emailVal,
        phoneVal,
        webCell,
        r.category || "General Business",
        ratingCell,
        socialsVal,
        mapsCell,
        addressVal,
        r.quality_score !== undefined ? r.quality_score : 50
      ]);
    }

    if (newValues.length > 0) {
      const targetRange = sheet.getRange(startRow, 1, newValues.length, 11);
      targetRange.setValues(newValues);
      formatDataRows(sheet, startRow, newValues.length);
    }

    return ContentService.createTextOutput(JSON.stringify({
      status: "success",
      sheet_id: sheetId,
      sheet_url: ss.getUrl(),
      total_rows: sheet.getLastRow() - 2
    })).setMimeType(ContentService.MimeType.JSON);

  } catch (error) {
    return ContentService.createTextOutput(JSON.stringify({
      status: "error",
      message: error.toString()
    })).setMimeType(ContentService.MimeType.JSON);
  }
}

/**
 * Sets up the single-row Master Bar (Row 1), Sticky Header (Row 2), and Freezes Columns 1-2.
 */
function setupSheetLayout(sheet, topic) {
  sheet.setName("Lead Directory");
  sheet.clear();

  // Explicit column widths (11 columns matching exact requested hierarchy)
  const colWidths = [
    50,   // 1. #
    250,  // 2. Business Name
    240,  // 3. Email Address
    160,  // 4. Phone Number
    200,  // 5. Website
    170,  // 6. Category
    140,  // 7. Rating & Reviews (Merged)
    230,  // 8. Social Profiles
    120,  // 9. Google Maps
    280,  // 10. Full Address
    110   // 11. Lead Quality Score (At the very end)
  ];

  for (let c = 0; c < colWidths.length; c++) {
    sheet.setColumnWidth(c + 1, colWidths[c]);
  }

  // Row 1: Single Compact Master Bar (Topic on Left + Live KPI Badges with %)
  sheet.setRowHeight(1, 38);

  // 1. Title Banner (Cols 1-2) - High-End Dark Obsidian Slate (#111827) for clear contrast against Row 2
  // Must ONLY merge cols 1-2 so it stays strictly within the 2 frozen columns!
  sheet.getRange(1, 1, 1, 2).merge();
  const banner = sheet.getRange(1, 1);
  banner.setValue("📊 " + topic.toUpperCase());
  banner.setBackground("#111827");
  banner.setFontColor("#FFFFFF");
  banner.setFontFamily("Google Sans, Roboto, Inter, Arial");
  banner.setFontSize(11);
  banner.setFontWeight("bold");
  banner.setHorizontalAlignment("center");
  banner.setVerticalAlignment("middle");

  // 2. KPI Badge 1: Total Leads (Cols 3-4)
  sheet.getRange(1, 3, 1, 2).merge();
  const card1 = sheet.getRange(1, 3);
  card1.setFormula('="👥 TOTAL: " & COUNTA(A3:A)');
  styleKpiBadge(card1, "#E8F0FE", "#1967D2", "#4285F4");

  // 3. KPI Badge 2: Emails Found % (Cols 5-6)
  sheet.getRange(1, 5, 1, 2).merge();
  const card2 = sheet.getRange(1, 5);
  card2.setFormula('="✉️ EMAILS: " & TEXT(COUNTIF(C3:C, "<>NOT FOUND") / MAX(1, COUNTA(A3:A)), "0.0%")');
  styleKpiBadge(card2, "#E6F4EA", "#137333", "#34A853");

  // 4. KPI Badge 3: Phones Verified % (Cols 7-8)
  sheet.getRange(1, 7, 1, 2).merge();
  const card3 = sheet.getRange(1, 7);
  card3.setFormula('="📞 PHONES: " & TEXT(COUNTIF(D3:D, "<>NOT FOUND") / MAX(1, COUNTA(A3:A)), "0.0%")');
  styleKpiBadge(card3, "#FEF7E0", "#B06000", "#FBBC04");

  // 5. KPI Badge 4: Top Rated % (Cols 9-11)
  sheet.getRange(1, 9, 1, 3).merge();
  const card4 = sheet.getRange(1, 9);
  card4.setFormula('="⭐ TOP RATED: " & TEXT(COUNTIF(G3:G, "*5.0*") + COUNTIF(G3:G, "*4.9*") + COUNTIF(G3:G, "*4.8*"), "#") & " (" & TEXT((COUNTIF(G3:G, "*5.0*") + COUNTIF(G3:G, "*4.9*") + COUNTIF(G3:G, "*4.8*")) / MAX(1, COUNTA(A3:A)), "0%") & ")"');
  styleKpiBadge(card4, "#FCE8E6", "#C5221F", "#EA4335");

  // Row 2: Sticky Frozen Header with User-Requested Hierarchy
  const headers = [
    "#",
    "Business Name",
    "Email Address",
    "Phone Number",
    "Website",
    "Category",
    "Rating & Reviews",
    "Social Profiles",
    "Google Maps",
    "Full Address",
    "Quality Score"
  ];

  // Distinct Google-themed colors per column header (Business Name in Google Blue #1A73E8 contrasts with Obsidian Row 1)
  const headerColors = [
    "#0F172A", // 1. #
    "#1A73E8", // 2. Name (Google Blue)
    "#137333", // 3. Email (Google Green)
    "#B06000", // 4. Phone (Google Amber)
    "#185ABC", // 5. Website (Google Sapphire)
    "#5F6368", // 6. Category (Google Slate)
    "#C5221F", // 7. Rating (Google Red)
    "#7B1FA2", // 8. Socials (Google Purple)
    "#0288D1", // 9. Maps (Google Cerulean)
    "#374151", // 10. Address (Dark Slate)
    "#D93025"  // 11. Quality Score (Crimson Badge)
  ];

  sheet.setRowHeight(2, 32);
  for (let c = 0; c < headers.length; c++) {
    const hCell = sheet.getRange(2, c + 1);
    hCell.setValue(headers[c]);
    hCell.setBackground(headerColors[c]);
    hCell.setFontColor("#FFFFFF");
    hCell.setFontFamily("Google Sans, Roboto, Inter, Arial");
    hCell.setFontSize(10);
    hCell.setFontWeight("bold");
    hCell.setHorizontalAlignment("center");
    hCell.setVerticalAlignment("middle");
  }

  // Freeze top 2 rows AND freeze first 2 columns (Sticky Business Names on horizontal scroll!)
  try {
    sheet.setFrozenRows(2);
    sheet.setFrozenColumns(2);
  } catch (fzErr) {
    try {
      sheet.setFrozenRows(2);
    } catch (e) {}
  }

  // Strict text clipping across entire sheet so text NEVER spills out of its cell
  try {
    sheet.getRange(1, 1, Math.max(100, sheet.getMaxRows()), 11).setWrapStrategy(SpreadsheetApp.WrapStrategy.CLIP);
  } catch (clipErr) {}
}

function styleKpiBadge(range, bgColor, fontColor, borderColor) {
  range.setBackground(bgColor);
  range.setFontColor(fontColor);
  range.setFontFamily("Google Sans, Roboto, Inter, Arial");
  range.setFontSize(10);
  range.setFontWeight("bold");
  range.setHorizontalAlignment("center");
  range.setVerticalAlignment("middle");
  range.setBorder(true, true, true, true, true, true, borderColor, SpreadsheetApp.BorderStyle.SOLID_MEDIUM);
}

/**
 * Formats data rows with top-to-bottom color-coded columns per information type,
 * handles "NOT FOUND" cells with crisp red badges and white text, and strict text clipping.
 */
function formatDataRows(sheet, startRow, rowCount) {
  const range = sheet.getRange(startRow, 1, rowCount, 11);
  range.setFontFamily("Roboto, Inter, Arial");
  range.setFontSize(9);
  range.setVerticalAlignment("middle");
  
  // Strict CLIP: guarantees NO text ever bleeds outside of its cell boundary
  range.setWrapStrategy(SpreadsheetApp.WrapStrategy.CLIP);

  // Subtle clean cell grid borders (#E0E0E0)
  range.setBorder(true, true, true, true, true, true, "#E0E0E0", SpreadsheetApp.BorderStyle.SOLID);

  // Baseline per-column styling:
  sheet.getRange(startRow, 1, rowCount, 1).setBackground("#F1F3F4").setFontColor("#5F6368").setHorizontalAlignment("center");
  sheet.getRange(startRow, 2, rowCount, 1).setBackground("#FFFFFF").setFontColor("#1E293B").setFontWeight("bold").setHorizontalAlignment("left");
  sheet.getRange(startRow, 3, rowCount, 1).setBackground("#E6F4EA").setFontColor("#0D652D").setFontWeight("bold").setHorizontalAlignment("left");
  sheet.getRange(startRow, 4, rowCount, 1).setBackground("#FEF7E0").setFontColor("#202124").setFontWeight("bold").setHorizontalAlignment("center");
  sheet.getRange(startRow, 5, rowCount, 1).setBackground("#E8F0FE").setFontColor("#1A73E8").setHorizontalAlignment("left");
  sheet.getRange(startRow, 6, rowCount, 1).setBackground("#F8F9FA").setFontColor("#5F6368").setHorizontalAlignment("left");
  sheet.getRange(startRow, 7, rowCount, 1).setBackground("#FCE8E6").setFontColor("#C5221F").setFontWeight("bold").setHorizontalAlignment("center");
  sheet.getRange(startRow, 8, rowCount, 1).setBackground("#F3E8FD").setFontColor("#6A1B9A").setHorizontalAlignment("left");
  sheet.getRange(startRow, 9, rowCount, 1).setBackground("#E8F0FE").setFontColor("#1A73E8").setFontWeight("bold").setHorizontalAlignment("center");
  sheet.getRange(startRow, 10, rowCount, 1).setBackground("#FFFFFF").setFontColor("#3C4043").setHorizontalAlignment("left");
  sheet.getRange(startRow, 11, rowCount, 1).setBackground("#FEEAE6").setFontColor("#D93025").setFontWeight("bold").setHorizontalAlignment("center");

  // Scan for "NOT FOUND" cells and apply high-contrast Red Badge styling
  const values = range.getValues();
  for (let r = 0; r < rowCount; r++) {
    const curRow = startRow + r;
    sheet.setRowHeight(curRow, 26);

    for (let c = 0; c < 11; c++) {
      const val = String(values[r][c] || "").trim();
      if (val === "NOT FOUND") {
        const cell = sheet.getRange(curRow, c + 1);
        cell.setBackground("#D93025");  // Google Alert Red
        cell.setFontColor("#FFFFFF");   // Pure White text
        cell.setFontWeight("bold");
        cell.setHorizontalAlignment("center");
      }
    }
  }
}
