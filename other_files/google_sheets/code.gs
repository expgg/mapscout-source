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
    const discoveredEmails = {};

    for (let i = 0; i < rows.length; i++) {
      const r = rows[i];

      // Format Website hyperlink or NOT FOUND
      let webCell = "NOT FOUND";
      let cleanSiteUrl = "";
      if (r.website && r.website !== "N/A" && r.website !== "NOT FOUND" && r.website.startsWith("http")) {
        cleanSiteUrl = r.website;
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

      // Google Cloud Email Recovery Fallback:
      // If local scraper failed (residential IP block) and we are streaming (mode === "append"),
      // use Google Cloud's whitelisted datacenter IP to fetch emails!
      let emailVal = (r.email && r.email !== "N/A" && r.email !== "NOT FOUND") ? r.email : "NOT FOUND";
      if (emailVal === "NOT FOUND" && cleanSiteUrl && mode === "append") {
        try {
          const cloudEmail = fetchEmailFromGoogleCloud(cleanSiteUrl);
          if (cloudEmail) {
            emailVal = cloudEmail;
            discoveredEmails[r.business_name] = cloudEmail;
            if (r.quality_score !== undefined && r.quality_score < 75) {
              r.quality_score += 25;
            }
          }
        } catch (cloudErr) {}
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

      const phoneVal = (r.phone && r.phone !== "N/A" && r.phone !== "NOT FOUND") ? r.phone : "NOT FOUND";
      const socialsVal = (r.social_profiles && r.social_profiles !== "N/A" && r.social_profiles !== "NOT FOUND") ? r.social_profiles : "NOT FOUND";
      const addressVal = (r.address && r.address !== "N/A" && r.address !== "NOT FOUND") ? r.address : "NOT FOUND";

      // Column Hierarchy:
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
      total_rows: sheet.getLastRow() - 2,
      discovered_emails: discoveredEmails
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
  card2.setFormula('="✉️ EMAILS: " & TEXT(COUNTIFS(A3:A, "<>", C3:C, "<>", C3:C, "<>NOT FOUND") / MAX(1, COUNTA(A3:A)), "0.0%")');
  styleKpiBadge(card2, "#E6F4EA", "#137333", "#34A853");

  // 4. KPI Badge 3: Phones Verified % (Cols 7-8)
  sheet.getRange(1, 7, 1, 2).merge();
  const card3 = sheet.getRange(1, 7);
  card3.setFormula('="📞 PHONES: " & TEXT(COUNTIFS(A3:A, "<>", D3:D, "<>", D3:D, "<>NOT FOUND") / MAX(1, COUNTA(A3:A)), "0.0%")');
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

  // Initialize dynamic conditional formatting rules
  setupConditionalFormatting(sheet);
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
 * Sets up dynamic Conditional Formatting rules across the data range.
 * Automatically paints any "NOT FOUND" cell in Alert Red (#D93025) with bold white text.
 * As soon as any value is typed or pasted into the cell, the rule stops applying instantly,
 * restoring the column's proper background and font color without any manual intervention!
 */
function setupConditionalFormatting(sheet) {
  const maxRows = Math.max(1000, sheet.getMaxRows());
  const dataRange = sheet.getRange(3, 1, maxRows - 2, 11);

  const notFoundRule = SpreadsheetApp.newConditionalFormatRule()
    .whenTextEqualTo("NOT FOUND")
    .setBackground("#D93025")
    .setFontColor("#FFFFFF")
    .setBold(true)
    .setRanges([dataRange])
    .build();

  const rules = sheet.getConditionalFormatRules() || [];
  const cleanRules = rules.filter(r => {
    try {
      return r.getCriteriaType() !== SpreadsheetApp.BooleanCriteria.TEXT_EQUAL_TO;
    } catch (e) {
      return true;
    }
  });
  cleanRules.push(notFoundRule);
  sheet.setConditionalFormatRules(cleanRules);
}

/**
 * Formats data rows with top-to-bottom color-coded columns per information type,
 * and sets up dynamic conditional formatting so "NOT FOUND" turns red, and typing/pasting
 * data automatically adopts the column's theme.
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

  for (let r = 0; r < rowCount; r++) {
    sheet.setRowHeight(startRow + r, 26);
  }

  // Ensure dynamic conditional formatting is active across the dataset
  setupConditionalFormatting(sheet);
}

/**
 * Auto-detects manual edits or pasted content in the sheet.
 * If user edits or pastes a value into any data cell, automatically:
 * 1. Checks if the value is "NOT FOUND" (formats as red alert badge).
 * 2. If valid content is pasted/typed, automatically applies the column's specific color theme!
 * 3. If an email is pasted in Column 3, updates Quality Score in Col 11 (+25)!
 */
function onEdit(e) {
  if (!e || !e.range) return;
  const range = e.range;
  const sheet = range.getSheet();
  if (sheet.getName() !== "Lead Directory") return;
  
  const startRow = range.getRow();
  if (startRow < 3) return; // Skip master bar & header
  
  const numRows = range.getNumRows();
  const numCols = range.getNumCols();
  const startCol = range.getColumn();
  
  // Style mapping for columns 1-11
  const colStyles = {
    1: { bg: "#F1F3F4", font: "#5F6368", bold: false, align: "center" },
    2: { bg: "#FFFFFF", font: "#1E293B", bold: true, align: "left" },
    3: { bg: "#E6F4EA", font: "#0D652D", bold: true, align: "left" },    // Email
    4: { bg: "#FEF7E0", font: "#202124", bold: true, align: "center" },  // Phone
    5: { bg: "#E8F0FE", font: "#1A73E8", bold: false, align: "left" },   // Website
    6: { bg: "#F8F9FA", font: "#5F6368", bold: false, align: "left" },   // Category
    7: { bg: "#FCE8E6", font: "#C5221F", bold: true, align: "center" },  // Rating
    8: { bg: "#F3E8FD", font: "#6A1B9A", bold: false, align: "left" },   // Socials
    9: { bg: "#E8F0FE", font: "#1A73E8", bold: true, align: "center" },  // Maps
    10: { bg: "#FFFFFF", font: "#3C4043", bold: false, align: "left" },  // Address
    11: { bg: "#FEEAE6", font: "#D93025", bold: true, align: "center" }  // Score
  };
  
  const values = range.getValues();
  for (let r = 0; r < numRows; r++) {
    const curRow = startRow + r;
    for (let c = 0; c < numCols; c++) {
      const curCol = startCol + c;
      if (curCol > 11) continue;
      const cell = sheet.getRange(curRow, curCol);
      const val = String(values[r][c] || "").trim();
      
      if (val === "NOT FOUND") {
        cell.setBackground("#D93025");
        cell.setFontColor("#FFFFFF");
        cell.setFontWeight("bold");
        cell.setHorizontalAlignment("center");
      } else if (val !== "") {
        const style = colStyles[curCol];
        if (style) {
          cell.setBackground(style.bg);
          cell.setFontColor(style.font);
          cell.setFontWeight(style.bold ? "bold" : "normal");
          cell.setHorizontalAlignment(style.align);
        }
        // If user manually pasted an email into column 3, bump quality score in Col 11
        if (curCol === 3 && val.includes("@")) {
          const scoreCell = sheet.getRange(curRow, 11);
          const curScore = Number(scoreCell.getValue()) || 50;
          if (curScore < 75) {
            scoreCell.setValue(Math.min(100, curScore + 25));
          }
        }
      }
    }
  }
}

/**
 * =========================================================================
 *              GOOGLE CLOUD IP EMAIL EXTRACTION ENGINE
 * Uses Google's whitelisted datacenter IPs (UrlFetchApp) to bypass Cloudflare
 * and extract emails from websites without residential IP restrictions.
 * =========================================================================
 */

function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu("✦ MapScout Tools")
    .addItem("⚡ Scan Missing Emails via Google Cloud", "scanMissingEmailsInSheet")
    .addToUi();
}

/**
 * Manually scans any row in the current sheet where Email Address is "NOT FOUND"
 * but a valid Website URL exists, using Google Cloud's whitelisted IPs.
 */
function scanMissingEmailsInSheet() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getActiveSheet();
  const lastRow = sheet.getLastRow();
  if (lastRow < 3) {
    ss.toast("No lead data rows found to scan.", "MapScout Notice", 4);
    return;
  }

  const range = sheet.getRange(3, 1, lastRow - 2, 11);
  const values = range.getValues();
  const formulas = sheet.getRange(3, 5, lastRow - 2, 1).getFormulas();
  let recoveredCount = 0;

  for (let i = 0; i < values.length; i++) {
    const curEmail = String(values[i][2] || "").trim();
    if (curEmail === "NOT FOUND") {
      let rawSite = String(values[i][4] || "").trim();
      let formula = formulas[i][0] || "";

      let siteUrl = "";
      if (formula && formula.includes('HYPERLINK("')) {
        const m = formula.match(/HYPERLINK\("([^"]+)"/i);
        if (m) siteUrl = m[1];
      } else if (rawSite.startsWith("http")) {
        siteUrl = rawSite;
      }

      if (siteUrl && siteUrl.startsWith("http")) {
        try {
          const foundEmail = fetchEmailFromGoogleCloud(siteUrl);
          if (foundEmail) {
            const rowIndex = 3 + i;
            const emailCell = sheet.getRange(rowIndex, 3);
            emailCell.setValue(foundEmail);
            emailCell.setBackground("#E6F4EA");
            emailCell.setFontColor("#0D652D");
            emailCell.setFontWeight("bold");
            emailCell.setHorizontalAlignment("left");

            // Bump quality score by 25 points
            const scoreCell = sheet.getRange(rowIndex, 11);
            const curScore = Number(scoreCell.getValue()) || 50;
            if (curScore < 75) {
              scoreCell.setValue(Math.min(100, curScore + 25));
            }
            recoveredCount++;
          }
        } catch (e) {}
      }
    }
  }

  ss.toast("Scan complete! Recovered " + recoveredCount + " new emails via Google Cloud.", "MapScout Success", 6);
}

/**
 * Fetches target website using Google Datacenter IP, decoding Cloudflare & HTML entities.
 */
function fetchEmailFromGoogleCloud(siteUrl) {
  if (!siteUrl || !siteUrl.startsWith("http")) return "";

  const options = {
    muteHttpExceptions: true,
    followRedirects: true,
    validateHttpsCertificates: false,
    headers: {
      "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
      "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    }
  };

  try {
    // 1. Fetch homepage
    const response = UrlFetchApp.fetch(siteUrl, options);
    if (response.getResponseCode() === 200) {
      const htmlText = response.getContentText();
      const em = extractEmailFromHtml(htmlText);
      if (em) return em;

      // 2. Discover subpages: /contact, /about
      const subpaths = ["/contact", "/contact-us", "/about", "/about-us"];
      const baseClean = siteUrl.replace(/\/+$/, "");
      for (let s = 0; s < subpaths.length; s++) {
        try {
          const subResp = UrlFetchApp.fetch(baseClean + subpaths[s], options);
          if (subResp.getResponseCode() === 200) {
            const subEm = extractEmailFromHtml(subResp.getContentText());
            if (subEm) return subEm;
          }
        } catch (subErr) {}
      }
    }
  } catch (err) {}

  return "";
}

/**
 * Multi-pattern email extractor for Google Apps Script (Cloudflare hex + mailto + regex).
 */
function extractEmailFromHtml(rawHtml) {
  if (!rawHtml) return "";

  const junkExts = [".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".css", ".js", ".woff"];
  const junkSubs = ["sentry", "wix", "example.com", "yourdomain", "company.com", "your@email.com", "user@domain.com", "email@domain.com", "bootstrap", "cloudflare", "npm@", "react@"];

  function isValid(email) {
    if (!email || !email.includes("@")) return false;
    const e = email.toLowerCase().trim().replace(/\.+$/, "");
    for (let j = 0; j < junkExts.length; j++) {
      if (e.endsWith(junkExts[j])) return false;
    }
    for (let k = 0; k < junkSubs.length; k++) {
      if (e.includes(junkSubs[k])) return false;
    }
    const parts = e.split("@");
    if (parts.length !== 2 || parts[0].length < 1 || parts[1].length < 3) return false;
    if (!parts[1].includes(".")) return false;
    return true;
  }

  // 1. Cloudflare hex decoding
  const cfMatches = rawHtml.match(/data-cfemail="([a-f0-9]+)"/gi) || [];
  for (let c = 0; c < cfMatches.length; c++) {
    const hex = cfMatches[c].replace(/^data-cfemail="/i, "").replace(/"$/, "");
    try {
      const r = parseInt(hex.substr(0, 2), 16);
      let dec = "";
      for (let n = 2; n < hex.length; n += 2) {
        dec += String.fromCharCode(parseInt(hex.substr(n, 2), 16) ^ r);
      }
      if (isValid(dec)) return dec;
    } catch (ex) {}
  }

  // 2. Mailto anchors
  const mailtoMatches = rawHtml.match(/mailto:([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)/gi) || [];
  for (let m = 0; m < mailtoMatches.length; m++) {
    const rawM = mailtoMatches[m].replace(/^mailto:/i, "").split("?")[0].trim();
    if (isValid(rawM)) return rawM;
  }

  // 3. Normalized regex search
  const textMatches = rawHtml.match(/[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+/gi) || [];
  for (let t = 0; t < textMatches.length; t++) {
    const e = textMatches[t].trim();
    if (isValid(e)) return e;
  }

  return "";
}
