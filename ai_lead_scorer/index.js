require('dotenv').config();
const fs = require('fs');
const { parse } = require('csv-parse/sync');
const { stringify } = require('csv-stringify/sync');
const puppeteer = require('puppeteer');
const { GoogleGenAI } = require('@google/genai');

const ai = new GoogleGenAI({ apiKey: process.env.GEMINI_API_KEY });

const INPUT_CSV = '../fb_reels_dog_bot/Datasets/2026_10_02_v1_master.csv';
const OUTPUT_CSV = 'scored_leads_final.csv';
const CONCURRENCY = 3;

async function extractText(url, browser) {
    let page;
    try {
        page = await browser.newPage();
        await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 15000 });
        const text = await page.evaluate(() => document.body.innerText.slice(0, 8000));
        return text;
    } catch (e) {
        return null; // Inactive or blocked
    } finally {
        if (page) await page.close();
    }
}

async function analyzeWebsite(url, text) {
    if (!text) return { active: false, is_seller: false, has_form: false, has_kit: false, has_store: false };
    
    const prompt = `
Analyze the following text extracted from a website (${url}):
"""
${text}
"""

Extract the following information and return ONLY a valid JSON object:
{
  "is_seller": boolean, // True if this website sells dogs or puppies (breeders, kennels)
  "has_form": boolean, // True if they mention a puppy application, registration form, or waiting list form
  "has_kit": boolean, // True if they mention a "take-home kit", "starter kit", "puppy pack", etc.
  "has_store": boolean // True if they have an online store for pet supplies/merchandise
}
`;
    try {
        const response = await ai.models.generateContent({
            model: 'gemini-flash-lite-latest',
            contents: prompt,
            config: {
                responseMimeType: 'application/json',
            }
        });
        return JSON.parse(response.text);
    } catch (e) {
        console.error(`AI Error for ${url}:`, e.message);
        return { active: true, is_seller: false, has_form: false, has_kit: false, has_store: false };
    }
}

function classifyLead(row, aiResult) {
    const has_website = !!row.websites && aiResult.active;
    const has_contact = !!row.phones || !!row.emails;
    const has_social = !!row.facebook_url || !!row.instagram;
    
    // Parse stats
    const followers = parseInt((row.followers || '').replace(/\D/g, '')) || 0;
    const likes = parseInt((row.likes || '').replace(/\D/g, '')) || 0;
    const reviews = parseInt((row.google_review_count || '').replace(/\D/g, '')) || 0;
    
    const social_active = has_social && (followers > 500 || likes > 500);
    const large_scale = reviews > 20 || followers > 2000 || likes > 2000;
    
    if (has_website) {
        if (aiResult.is_seller) {
            if (social_active && large_scale) return 'A';
            if (has_contact) return 'B';
            return 'C';
        } else {
            if (has_contact) return 'B'; // Has contact but maybe not a direct puppy seller
            return 'D';
        }
    } else {
        if (row.google_maps_url || row.facebook_url) return 'C';
        return 'D';
    }
}

async function main() {
    if (!process.env.GEMINI_API_KEY) {
        console.error("Please set GEMINI_API_KEY in a .env file.");
        process.exit(1);
    }
    
    const fileData = fs.readFileSync(INPUT_CSV, 'utf8');
    const records = parse(fileData, { columns: true, skip_empty_lines: true });
    
    let processed = 0;
    const browser = await puppeteer.launch({ headless: true });
    
    console.log(`Loaded ${records.length} records. Starting AI Lead Scoring...`);
    
    const outData = [];
    
    // Process in batches
    for (let i = 0; i < records.length; i += CONCURRENCY) {
        const batch = records.slice(i, i + CONCURRENCY);
        
        const promises = batch.map(async (row) => {
            let aiResult = { active: false, is_seller: false, has_form: false, has_kit: false, has_store: false };
            const url = (row.websites || row.resolved_urls || '').split('|')[0].trim();
            
            if (url && url.startsWith('http')) {
                const text = await extractText(url, browser);
                if (text) {
                    aiResult = await analyzeWebsite(url, text);
                    aiResult.active = true;
                }
            }
            
            const leadClass = classifyLead(row, aiResult);
            
            const result = {
                ...row,
                WebsiteActive: aiResult.active ? 'Yes' : 'No',
                IsPuppySeller: aiResult.is_seller ? 'Yes' : 'No',
                HasForm: aiResult.has_form ? 'Yes' : 'No',
                HasTakeHomeKit: aiResult.has_kit ? 'Yes' : 'No',
                HasPetStore: aiResult.has_store ? 'Yes' : 'No',
                AIClass: leadClass
            };
            
            console.log(`[Scored] ${url} -> Seller: ${aiResult.is_seller}, Form: ${aiResult.has_form}, Kit: ${aiResult.has_kit}, Class: ${leadClass}`);
            return result;
        });
        
        const results = await Promise.all(promises);
        outData.push(...results);
        
        processed += results.length;
        console.log(`Processed ${processed} / ${records.length}...`);
        
        // Rate Limit Handling for free tier Gemini API (15 RPM -> Max 3 reqs / 12 seconds)
        await new Promise(r => setTimeout(r, 12500));

        // Save intermediate results every 50 records
        if (processed % 50 === 0 || processed >= records.length) {
            fs.writeFileSync(OUTPUT_CSV, stringify(outData, { header: true }));
        }
    }
    
    await browser.close();
    console.log(`Done! Results saved to ${OUTPUT_CSV}`);
}

main();
