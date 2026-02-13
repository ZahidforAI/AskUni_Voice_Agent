"""
SMIU Voice Agent Server - FastAPI Version
Serves frontend (index.html) + WebSocket for RAG.
Designed for deployment on Render.
"""

import asyncio
import json
import re
import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from groq_rag import get_groq_response, create_vector_db

app = FastAPI()

# Ensure vector database exists
DB_PATH = "./faiss_index"

# ============================================================================
# URL Mappings (Maintained for logic)
# ============================================================================
# [SMIU, NED, IBA, UOK, FAST, SZABIST, DHA_SUFFA, DUET URL mappings here...]
# (I'll keep them as they are in the original file)

# ... (rest of the URL mappings and clean_text_for_tts/detect_navigation_request functions)
# For brevity in the edit, I'll assume the full logic is preserved below.

# ============================================================================
# SMIU URL Mappings
# ============================================================================
SMIU_URLS = {
    # Main pages
    "home": "https://smiu.edu.pk/",
    "main": "https://smiu.edu.pk/",
    "smiu website": "https://smiu.edu.pk/",
    "website": "https://smiu.edu.pk/",
    
    # Admissions
    "admission": "https://smiu.edu.pk/admissions",
    "admissions": "https://smiu.edu.pk/admissions",
    "apply": "https://smiu.edu.pk/admissions",
    "enrollment": "https://smiu.edu.pk/admissions",
    "admission form": "https://smiu.edu.pk/admissions",
    
    # Academics
    "programs": "https://www.smiu.edu.pk/admissions/undergraduate-programs",
    "courses": "https://www.smiu.edu.pk/admissions/undergraduate-programs",
    "departments": "https://www.smiu.edu.pk/academics/departments",
    "faculty": "https://www.smiu.edu.pk/resources/staff",
    "academics": "https://www.smiu.edu.pk/students/academic-calendar",
    
    # Specific departments
    "computer science": "https://www.smiu.edu.pk/cs/bscs_program",
    "cs department": "https://www.smiu.edu.pk/cs/bscs_program",
    "cyber security": "https://www.smiu.edu.pk/cs/bs-cyber-security",
    "ai": "https://www.smiu.edu.pk/aiams/artificial-intelligence-mathematical-sciences",
    "business": "https://www.smiu.edu.pk/Business/bba-program",
    "bba": "https://www.smiu.edu.pk/Business/bba-program",
    "mba": "https://www.smiu.edu.pk/Business/mba-program",
    
    # Student resources
    "fee": "https://smiu.edu.pk/admissions/fee-structure",
    "fees": "https://smiu.edu.pk/admissions/fee-structure",
    "fee structure": "https://smiu.edu.pk/admissions/fee-structure",
    "scholarship": "https://smiu.edu.pk/admissions/scholarships",
    "scholarships": "https://smiu.edu.pk/admissions/scholarships",
    "financial aid": "https://smiu.edu.pk/admissions/scholarships",
    
    # Campus & facilities
    "library": "https://www.smiu.edu.pk/Library",
    "facilities": "https://www.smiu.edu.pk/students/facilities-at-smiu",
    "hostel": "https://www.smiu.edu.pk/students/facilities-at-smiu",
    
    # Contact & about
    "contact": "https://www.smiu.edu.pk/cpe/contact-us",
    "contact us": "https://www.smiu.edu.pk/cpe/contact-us",
    "about": "https://www.smiu.edu.pk/about",
    "about us": "https://www.smiu.edu.pk/about",
    "history": "https://www.smiu.edu.pk/about/history",
    
    # Student portals
    "portal": "http://cms.smiu.edu.pk:9991/psp/ps/?cmd=login",
    "student portal": "http://cms.smiu.edu.pk:9991/psp/ps/?cmd=login",
    "cms": "http://cms.smiu.edu.pk:9991/psp/ps/?cmd=login",
    
    # News & events
    "news": "https://www.smiu.edu.pk/viewnews",
    "announcements": "https://www.smiu.edu.pk/viewnews",
}

# ============================================================================
# NED UNIVERSITY OF ENGINEERING & TECHNOLOGY
# ============================================================================
NED_URLS = {
    # Main pages
    "home": "https://www.neduet.edu.pk/",
    "main": "https://www.neduet.edu.pk/",
    "ned website": "https://www.neduet.edu.pk/",
    "website": "https://www.neduet.edu.pk/",
    
    # Admissions
    "admission": "https://www.neduet.edu.pk/admissions",
    "admissions": "https://www.neduet.edu.pk/admissions",
    "apply": "https://www.neduet.edu.pk/admissions",
    "enrollment": "https://www.neduet.edu.pk/admissions",
    "admission form": "https://www.neduet.edu.pk/admissions",
    "undergraduate admission": "https://www.neduet.edu.pk/undergraduate",
    "graduate admission": "https://www.neduet.edu.pk/graduate",
    
    # Academics
    "programs": "https://www.neduet.edu.pk/academics/programs",
    "courses": "https://www.neduet.edu.pk/academics/programs",
    "departments": "https://www.neduet.edu.pk/academics/departments",
    "faculty": "https://www.neduet.edu.pk/faculty",
    "academics": "https://www.neduet.edu.pk/academics",
    
    # Departments/Faculties
    "civil engineering": "https://www.neduet.edu.pk/civil",
    "mechanical engineering": "https://www.neduet.edu.pk/mechanical",
    "electrical engineering": "https://www.neduet.edu.pk/electrical",
    "computer science": "https://www.neduet.edu.pk/computer-science",
    "petroleum engineering": "https://www.neduet.edu.pk/petroleum",
    
    # Student resources
    "fee": "https://www.neduet.edu.pk/fee-structure",
    "fees": "https://www.neduet.edu.pk/fee-structure",
    "fee structure": "https://www.neduet.edu.pk/fee-structure",
    "scholarship": "https://www.neduet.edu.pk/scholarships",
    "scholarships": "https://www.neduet.edu.pk/scholarships",
    "financial aid": "https://www.neduet.edu.pk/scholarships",
    
    # Campus & facilities
    "library": "https://www.neduet.edu.pk/library",
    "facilities": "https://www.neduet.edu.pk/facilities",
    "hostel": "https://www.neduet.edu.pk/hostel",
    "campus": "https://www.neduet.edu.pk/campus",
    
    # Contact & about
    "contact": "https://www.neduet.edu.pk/contact",
    "contact us": "https://www.neduet.edu.pk/contact",
    "about": "https://www.neduet.edu.pk/about",
    "about us": "https://www.neduet.edu.pk/about",
    "history": "https://www.neduet.edu.pk/history",
    
    # Student portals
    "portal": "https://www.neduet.edu.pk/portal",
    "student portal": "https://www.neduet.edu.pk/portal",
    
    # Examinations
    "examination": "https://www.neduet.edu.pk/examination",
    "results": "https://www.neduet.edu.pk/results",
    "exam schedule": "https://www.neduet.edu.pk/exam-schedule",
}

# ============================================================================
# IBA KARACHI (INSTITUTE OF BUSINESS ADMINISTRATION)
# ============================================================================
IBA_URLS = {
    # Main pages
    "home": "https://www.iba.edu.pk/",
    "main": "https://www.iba.edu.pk/",
    "iba website": "https://www.iba.edu.pk/",
    "website": "https://www.iba.edu.pk/",
    
    # Admissions
    "admission": "https://www.iba.edu.pk/admissions.php",
    "admissions": "https://www.iba.edu.pk/admissions.php",
    "apply": "https://www.iba.edu.pk/admissions.php",
    "enrollment": "https://www.iba.edu.pk/admissions.php",
    "admission form": "https://www.iba.edu.pk/admissions.php",
    "undergraduate admission": "https://www.iba.edu.pk/undergraduate-admissions.php",
    "graduate admission": "https://www.iba.edu.pk/graduate-admissions.php",
    
    # Academics
    "programs": "https://www.iba.edu.pk/programs.php",
    "courses": "https://www.iba.edu.pk/programs.php",
    "departments": "https://www.iba.edu.pk/departments.php",
    "faculty": "https://www.iba.edu.pk/faculty.php",
    "academics": "https://www.iba.edu.pk/academics.php",
    
    # Specific programs
    "bba": "https://www.iba.edu.pk/bba.php",
    "mba": "https://www.iba.edu.pk/mba.php",
    "business administration": "https://www.iba.edu.pk/bba.php",
    "computer science": "https://www.iba.edu.pk/computer-science.php",
    "economics": "https://www.iba.edu.pk/economics.php",
    "social sciences": "https://www.iba.edu.pk/social-sciences.php",
    
    # Student resources
    "fee": "https://www.iba.edu.pk/fee-structure.php",
    "fees": "https://www.iba.edu.pk/fee-structure.php",
    "fee structure": "https://www.iba.edu.pk/fee-structure.php",
    "scholarship": "https://www.iba.edu.pk/scholarships.php",
    "scholarships": "https://www.iba.edu.pk/scholarships.php",
    "financial aid": "https://www.iba.edu.pk/financial-aid.php",
    
    # Campus & facilities
    "library": "https://www.iba.edu.pk/library.php",
    "facilities": "https://www.iba.edu.pk/facilities.php",
    "hostel": "https://www.iba.edu.pk/hostel.php",
    "campus": "https://www.iba.edu.pk/campus.php",
    
    # Contact & about
    "contact": "https://www.iba.edu.pk/contact.php",
    "contact us": "https://www.iba.edu.pk/contact.php",
    "about": "https://www.iba.edu.pk/about.php",
    "about us": "https://www.iba.edu.pk/about.php",
    "history": "https://www.iba.edu.pk/history.php",
    
    # Student life
    "student life": "https://www.iba.edu.pk/student-life.php",
    "societies": "https://www.iba.edu.pk/societies.php",
    "events": "https://www.iba.edu.pk/events.php",
    
    # News & announcements
    "news": "https://www.iba.edu.pk/news.php",
    "announcements": "https://www.iba.edu.pk/announcements.php",
}

# ============================================================================
# UNIVERSITY OF KARACHI (UOK)
# ============================================================================
UOK_URLS = {
    # Main pages
    "home": "https://www.uok.edu.pk/",
    "main": "https://www.uok.edu.pk/",
    "ku website": "https://www.uok.edu.pk/",
    "uok website": "https://www.uok.edu.pk/",
    "website": "https://www.uok.edu.pk/",
    
    # Admissions
    "admission": "https://uokadmission.edu.pk/",
    "admissions": "https://uokadmission.edu.pk/",
    "apply": "https://uokadmission.edu.pk/",
    "enrollment": "https://uokadmission.edu.pk/",
    "admission form": "https://uokadmission.edu.pk/",
    "admission portal": "https://uokadmission.edu.pk/login",
    "undergraduate admission": "https://uokadmission.edu.pk/",
    
    # Academics
    "programs": "https://www.uok.edu.pk/faculties/programs.php",
    "courses": "https://www.uok.edu.pk/faculties/programs.php",
    "departments": "https://www.uok.edu.pk/faculties/departments.php",
    "faculty": "https://www.uok.edu.pk/faculties",
    "academics": "https://www.uok.edu.pk/academics.php",
    "faculties": "https://www.uok.edu.pk/faculties",
    
    # Specific faculties
    "arts": "https://www.uok.edu.pk/faculties/arts.php",
    "science": "https://www.uok.edu.pk/faculties/science.php",
    "engineering": "https://www.uok.edu.pk/faculties/engineering.php",
    "management": "https://www.uok.edu.pk/faculties/management.php",
    "pharmacy": "https://www.uok.edu.pk/faculties/pharmacy.php",
    "islamic studies": "https://www.uok.edu.pk/faculties/islamic-studies.php",
    "law": "https://www.uok.edu.pk/faculties/law.php",
    
    # Student resources
    "fee": "https://www.uok.edu.pk/admission/fee_structure.php",
    "fees": "https://www.uok.edu.pk/admission/fee_structure.php",
    "fee structure": "https://www.uok.edu.pk/admission/fee_structure.php",
    "scholarship": "https://www.uok.edu.pk/scholarships.php",
    "scholarships": "https://www.uok.edu.pk/scholarships.php",
    "financial aid": "https://www.uok.edu.pk/scholarships.php",
    
    # Campus & facilities
    "library": "https://www.uok.edu.pk/library",
    "facilities": "https://www.uok.edu.pk/facilities.php",
    "hostel": "https://www.uok.edu.pk/hostel.php",
    "campus": "https://www.uok.edu.pk/campus.php",
    
    # Contact & about
    "contact": "https://www.uok.edu.pk/contact_us.php",
    "contact us": "https://www.uok.edu.pk/contact_us.php",
    "about": "https://www.uok.edu.pk/aboutku.php",
    "about us": "https://www.uok.edu.pk/aboutku.php",
    "history": "https://www.uok.edu.pk/history.php",
    
    # Examination
    "examination": "https://www.uok.edu.pk/examination",
    "results": "https://www.uok.edu.pk/results.php",
    "exam schedule": "https://www.uok.edu.pk/examination/schedule.php",
    
    # News & events
    "news": "https://www.uok.edu.pk/news.php",
    "announcements": "https://www.uok.edu.pk/news.php",
    "events": "https://www.uok.edu.pk/events.php",
}

# ============================================================================
# FAST UNIVERSITY (NUCES) - KARACHI CAMPUS
# ============================================================================
FAST_URLS = {
    # Main pages
    "home": "https://khi.nu.edu.pk/",
    "main": "https://khi.nu.edu.pk/",
    "fast website": "https://khi.nu.edu.pk/",
    "nuces website": "https://nu.edu.pk/",
    "website": "https://khi.nu.edu.pk/",
    "national website": "https://nu.edu.pk/",
    
    # Admissions
    "admission": "https://admissions.nu.edu.pk/",
    "admissions": "https://admissions.nu.edu.pk/",
    "apply": "https://admissions.nu.edu.pk/",
    "enrollment": "https://admissions.nu.edu.pk/",
    "admission form": "https://admissions.nu.edu.pk/",
    "admission portal": "https://admissions.nu.edu.pk/",
    
    # Academics
    "programs": "https://khi.nu.edu.pk/Academics/Undergraduate",
    "courses": "https://khi.nu.edu.pk/Academics/Undergraduate",
    "departments": "https://khi.nu.edu.pk/Academics/Departments",
    "faculty": "https://khi.nu.edu.pk/Faculty",
    "academics": "https://khi.nu.edu.pk/Academics",
    
    # Specific programs
    "computer science": "https://khi.nu.edu.pk/Academics/BSCS",
    "software engineering": "https://khi.nu.edu.pk/Academics/BSSE",
    "electrical engineering": "https://khi.nu.edu.pk/Academics/BEE",
    "artificial intelligence": "https://khi.nu.edu.pk/Academics/AI",
    "data science": "https://khi.nu.edu.pk/Academics/DataScience",
    "cyber security": "https://khi.nu.edu.pk/Academics/CyberSecurity",
    "business administration": "https://khi.nu.edu.pk/Academics/BBA",
    
    # Student resources
    "fee": "https://khi.nu.edu.pk/Admissions/FeeStructure",
    "fees": "https://khi.nu.edu.pk/Admissions/FeeStructure",
    "fee structure": "https://khi.nu.edu.pk/Admissions/FeeStructure",
    "scholarship": "https://khi.nu.edu.pk/Admissions/Scholarships",
    "scholarships": "https://khi.nu.edu.pk/Admissions/Scholarships",
    "financial aid": "https://khi.nu.edu.pk/Admissions/FinancialAid",
    
    # Campus & facilities
    "library": "https://khi.nu.edu.pk/Campus/Library",
    "facilities": "https://khi.nu.edu.pk/Campus/Facilities",
    "hostel": "https://khi.nu.edu.pk/Campus/Hostel",
    "campus": "https://khi.nu.edu.pk/Campus",
    "main campus": "https://khi.nu.edu.pk/",
    "city campus": "https://khi.nu.edu.pk/CityCampus",
    
    # Contact & about
    "contact": "https://nu.edu.pk/home/ContactUs",
    "contact us": "https://nu.edu.pk/home/ContactUs",
    "about": "https://khi.nu.edu.pk/About",
    "about us": "https://khi.nu.edu.pk/About",
    "history": "https://khi.nu.edu.pk/About/History",
    
    # Student life
    "student life": "https://khi.nu.edu.pk/StudentLife",
    "societies": "https://khi.nu.edu.pk/StudentLife/Societies",
    "events": "https://khi.nu.edu.pk/Events",
    
    # News & announcements
    "news": "https://khi.nu.edu.pk/News",
    "announcements": "https://khi.nu.edu.pk/Announcements",
}

# ============================================================================
# SZABIST UNIVERSITY - KARACHI CAMPUS
# ============================================================================
SZABIST_URLS = {
    # Main pages
    "home": "https://szabist.edu.pk/",
    "main": "https://szabist.edu.pk/",
    "szabist website": "https://szabist.edu.pk/",
    "website": "https://szabist.edu.pk/",
    
    # Admissions
    "admission": "https://admissions.szabist.edu.pk/",
    "admissions": "https://admissions.szabist.edu.pk/",
    "apply": "https://admissions.szabist.edu.pk/",
    "enrollment": "https://admissions.szabist.edu.pk/",
    "admission form": "https://admissions.szabist.edu.pk/",
    "admission portal": "https://admissions.szabist.edu.pk/",
    
    # Academics
    "programs": "https://szabist.edu.pk/programs",
    "courses": "https://szabist.edu.pk/programs",
    "departments": "https://szabist.edu.pk/departments",
    "faculty": "https://szabist.edu.pk/faculty",
    "academics": "https://szabist.edu.pk/academics",
    
    # Specific programs
    "bba": "https://szabist.edu.pk/bba",
    "mba": "https://szabist.edu.pk/mba",
    "computer science": "https://szabist.edu.pk/computer-science",
    "software engineering": "https://szabist.edu.pk/software-engineering",
    "media sciences": "https://szabist.edu.pk/media-sciences",
    "mechatronics": "https://szabist.edu.pk/mechatronics",
    "accounting and finance": "https://szabist.edu.pk/accounting-finance",
    "cyber security": "https://szabist.edu.pk/cyber-security",
    
    # Student resources
    "fee": "https://szabist.edu.pk/fee-structure",
    "fees": "https://szabist.edu.pk/fee-structure",
    "fee structure": "https://szabist.edu.pk/fee-structure",
    "scholarship": "https://szabist.edu.pk/scholarships",
    "scholarships": "https://szabist.edu.pk/scholarships",
    "financial aid": "https://szabist.edu.pk/financial-aid",
    
    # Campus & facilities
    "library": "https://szabist.edu.pk/library",
    "facilities": "https://szabist.edu.pk/facilities",
    "hostel": "https://szabist.edu.pk/hostel",
    "campus": "https://szabist.edu.pk/campus",
    
    # Contact & about
    "contact": "https://admissions.szabist.edu.pk/contactus.aspx",
    "contact us": "https://admissions.szabist.edu.pk/contactus.aspx",
    "about": "https://szabist.edu.pk/about",
    "about us": "https://szabist.edu.pk/about",
    "history": "https://szabist.edu.pk/history",
    
    # Student portal
    "portal": "http://www.zabdesk.szabist.edu.pk/",
    "student portal": "http://www.zabdesk.szabist.edu.pk/",
    "zabdesk": "http://www.zabdesk.szabist.edu.pk/",
    
    # Student life
    "student life": "https://szabist.edu.pk/student-life",
    "societies": "https://szabist.edu.pk/societies",
    "events": "https://szabist.edu.pk/events",
    
    # News & announcements
    "news": "https://szabist.edu.pk/news",
    "announcements": "https://szabist.edu.pk/announcements",
}

# ============================================================================
# DHA SUFFA UNIVERSITY
# ============================================================================
DHA_SUFFA_URLS = {
    # Main pages
    "home": "https://www.dsu.edu.pk/",
    "main": "https://www.dsu.edu.pk/",
    "dsu website": "https://www.dsu.edu.pk/",
    "dha suffa website": "https://www.dsu.edu.pk/",
    "website": "https://www.dsu.edu.pk/",
    
    # Admissions
    "dha suffa admission": "https://www.dsu.edu.pk/admissions/",
    "admissions": "https://www.dsu.edu.pk/admissions/",
    "apply": "https://www.dsu.edu.pk/admissions/",
    "enrollment": "https://www.dsu.edu.pk/admissions/",
    "admission form": "https://www.dsu.edu.pk/admissions/",
    "undergraduate admission": "https://www.dsu.edu.pk/admissions/undergraduate/",
    "graduate admission": "https://www.dsu.edu.pk/admissions/graduate/",
    
    # Academics
    "programs": "https://www.dsu.edu.pk/academics/programs/",
    "courses": "https://www.dsu.edu.pk/academics/programs/",
    "departments": "https://www.dsu.edu.pk/academics/departments/",
    "faculty": "https://www.dsu.edu.pk/academics/faculty/",
    "academics": "https://www.dsu.edu.pk/academics/",
    
    # Specific programs
    "mechanical engineering": "https://www.dsu.edu.pk/mechanical-engineering/",
    "electrical engineering": "https://www.dsu.edu.pk/electrical-engineering/",
    "civil engineering": "https://www.dsu.edu.pk/civil-engineering/",
    "computer science": "https://www.dsu.edu.pk/computer-science/",
    "software engineering": "https://www.dsu.edu.pk/software-engineering/",
    "management sciences": "https://www.dsu.edu.pk/management-sciences/",
    "accounting and finance": "https://www.dsu.edu.pk/accounting-finance/",
    "business analytics": "https://www.dsu.edu.pk/business-analytics/",
    "data science": "https://www.dsu.edu.pk/data-science/",
    "psychology": "https://www.dsu.edu.pk/psychology/",
    "international relations": "https://www.dsu.edu.pk/international-relations/",
    
    # Student resources
    "fee": "https://www.dsu.edu.pk/admissions/fee-structure/",
    "fees": "https://www.dsu.edu.pk/admissions/fee-structure/",
    "fee structure": "https://www.dsu.edu.pk/admissions/fee-structure/",
    "scholarship": "https://www.dsu.edu.pk/admissions/scholarships/",
    "scholarships": "https://www.dsu.edu.pk/admissions/scholarships/",
    "financial aid": "https://www.dsu.edu.pk/admissions/financial-aid/",
    
    # Campus & facilities
    "library": "https://www.dsu.edu.pk/campus/library/",
    "facilities": "https://www.dsu.edu.pk/campus/facilities/",
    "hostel": "https://www.dsu.edu.pk/campus/hostel/",
    "campus": "https://www.dsu.edu.pk/campus/",
    "main campus": "https://www.dsu.edu.pk/",
    "dck campus": "https://www.dsu.edu.pk/dck-campus/",
    
    # Contact & about
    "contact": "https://www.dsu.edu.pk/contact/",
    "contact us": "https://www.dsu.edu.pk/contact/",
    "about": "https://www.dsu.edu.pk/about/",
    "about us": "https://www.dsu.edu.pk/about/",
    "history": "https://www.dsu.edu.pk/about/history/",
    "vision": "https://www.dsu.edu.pk/about/vision-mission/",
    "mission": "https://www.dsu.edu.pk/about/vision-mission/",
    
    # Student life
    "student life": "https://www.dsu.edu.pk/student-life/",
    "societies": "https://www.dsu.edu.pk/student-life/societies/",
    "events": "https://www.dsu.edu.pk/events/",
    
    # News & announcements
    "news": "https://www.dsu.edu.pk/news/",
    "announcements": "https://www.dsu.edu.pk/announcements/",
}

# ============================================================================
# DAWOOD UNIVERSITY OF ENGINEERING & TECHNOLOGY (DUET)
# ============================================================================
DUET_URLS = {
    # Main pages
    "home": "https://duet.edu.pk/",
    "main": "https://duet.edu.pk/",
    "duet website": "https://duet.edu.pk/",
    "website": "https://duet.edu.pk/",
    
    # Admissions
    "admission": "https://admissions.duet.edu.pk/",
    "admissions": "https://admissions.duet.edu.pk/",
    "apply": "https://admissions.duet.edu.pk/",
    "enrollment": "https://admissions.duet.edu.pk/",
    "admission form": "https://admissions.duet.edu.pk/",
    "admission portal": "https://admissions.duet.edu.pk/login",
    "application process": "https://admissions.duet.edu.pk/appprocess/",
    
    # Academics
    "programs": "https://duet.edu.pk/programs/",
    "courses": "https://duet.edu.pk/programs/",
    "departments": "https://duet.edu.pk/faculty-departments/",
    "faculty": "https://duet.edu.pk/faculty-departments/",
    "academics": "https://duet.edu.pk/academics/",
    
    # Specific departments
    "chemical engineering": "https://duet.edu.pk/chemical-engineering/",
    "petroleum engineering": "https://duet.edu.pk/petroleum-engineering/",
    "metallurgy": "https://duet.edu.pk/metallurgy/",
    "industrial engineering": "https://duet.edu.pk/industrial-engineering/",
    "computer science": "https://duet.edu.pk/computer-science/",
    "computer system engineering": "https://duet.edu.pk/computer-system-engineering/",
    "electronic engineering": "https://duet.edu.pk/electronic-engineering/",
    "telecommunication": "https://duet.edu.pk/telecommunication/",
    "cyber security": "https://duet.edu.pk/cyber-security/",
    "data science": "https://duet.edu.pk/data-science/",
    "artificial intelligence": "https://duet.edu.pk/artificial-intelligence/",
    "energy and environment": "https://duet.edu.pk/energy-environment/",
    
    # Student resources
    "fee": "https://duet.edu.pk/fee-structure/",
    "fees": "https://duet.edu.pk/fee-structure/",
    "fee structure": "https://duet.edu.pk/fee-structure/",
    "scholarship": "https://duet.edu.pk/scholarships/",
    "scholarships": "https://duet.edu.pk/scholarships/",
    "financial aid": "https://duet.edu.pk/financial-aid/",
    
    # Campus & facilities
    "library": "https://duet.edu.pk/library/",
    "facilities": "https://duet.edu.pk/facilities/",
    "hostel": "https://duet.edu.pk/hostel/",
    "campus": "https://duet.edu.pk/campus/",
    
    # Contact & about
    "contact": "https://duet.edu.pk/contact/",
    "contact us": "https://duet.edu.pk/contact/",
    "about": "https://duet.edu.pk/about/",
    "about us": "https://duet.edu.pk/about/",
    "history": "https://duet.edu.pk/history/",
    
    # Alumni
    "alumni": "https://alumni.duet.edu.pk/",
    "alumni portal": "https://alumni.duet.edu.pk/",
    
    # Prospectus
    "prospectus": "https://admissions.duet.edu.pk/prospectus/",
    
    # News & announcements
    "news": "https://duet.edu.pk/news/",
    "announcements": "https://admissions.duet.edu.pk/",
}

# Keywords that indicate user wants to open/navigate to a page
NAVIGATION_KEYWORDS = [
    "open", "go to", "take me to", "show me", "navigate to", 
    "visit", "browse", "launch", "access", "display",
    "open the", "go to the", "show the", "take me to the"
]

def clean_text_for_tts(text):
    """
    Remove markdown artifacts and separator lines that cause bad TTS experience.
    Removes: ________, --------, ========, ******, etc.
    """
    if not text:
        return ""
    
    # Remove long sequences of underscores, dashes, equals, asterisks (3 or more)
    text = re.sub(r'[_]{3,}', '', text)
    text = re.sub(r'[-]{3,}', '', text)
    text = re.sub(r'[=]{3,}', '', text)
    text = re.sub(r'[*]{3,}', '', text)
    
    # Remove markdown bold/italic markers
    text = text.replace('**', '').replace('__', '')
    
    return text.strip()

def detect_navigation_request(text):
    """
    Detect if user wants to navigate to a page.
    Returns (is_navigation, url, page_name, university_name) tuple.
    """
    text_lower = text.lower().strip()
    
    # Check if this is a navigation request
    is_navigation = any(keyword in text_lower for keyword in NAVIGATION_KEYWORDS)
    
    if not is_navigation:
        return False, None, None, None
    
    # Detect which university the user is referring to
    university_urls = None
    university_name = "SMIU"  # Default
    search_domain = "smiu.edu.pk"  # Default for search fallback
    
    if "ned" in text_lower:
        university_urls = NED_URLS
        university_name = "NED"
        search_domain = "neduet.edu.pk"
    elif "iba" in text_lower:
        university_urls = IBA_URLS
        university_name = "IBA"
        search_domain = "iba.edu.pk"
    elif any(x in text_lower for x in ["uok", "ku", "karachi university", "university of karachi"]):
        university_urls = UOK_URLS
        university_name = "University of Karachi"
        search_domain = "uok.edu.pk"
    elif any(x in text_lower for x in ["fast", "nuces"]):
        university_urls = FAST_URLS
        university_name = "FAST"
        search_domain = "khi.nu.edu.pk"
    elif "szabist" in text_lower:
        university_urls = SZABIST_URLS
        university_name = "SZABIST"
        search_domain = "szabist.edu.pk"
    elif any(x in text_lower for x in ["dha suffa", "dsu", "dha"]):
        university_urls = DHA_SUFFA_URLS
        university_name = "DHA Suffa"
        search_domain = "dsu.edu.pk"
    elif "duet" in text_lower or "dawood" in text_lower:
        university_urls = DUET_URLS
        university_name = "DUET"
        search_domain = "duet.edu.pk"
    elif "smiu" in text_lower:
        university_urls = SMIU_URLS
        university_name = "SMIU"
        search_domain = "smiu.edu.pk"
    else:
        # If no university specified, default to SMIU
        university_urls = SMIU_URLS
        university_name = "SMIU"
        search_domain = "smiu.edu.pk"
    
    # Find which page user wants to open
    for page_name, url in university_urls.items():
        if page_name in text_lower:
            return True, url, page_name, university_name
    
    # Special patterns for common requests
    if "admission" in text_lower and "admission" in university_urls:
        return True, university_urls["admission"], "admissions", university_name
    if "fee" in text_lower and "fee" in university_urls:
        return True, university_urls["fee"], "fee structure", university_name
    if "website" in text_lower or "page" in text_lower or "site" in text_lower or "home" in text_lower:
        return True, university_urls["home"], f"{university_name} website", university_name
    
    # Fallback: Dynamic Search
    # If we detected a navigation intent but didn't find a mapped URL, 
    # extract the topic and perform a site search.
    for keyword in NAVIGATION_KEYWORDS:
        if keyword in text_lower:
            # Remove the keyword to get the topic (e.g. "open library" -> "library")
            topic = text_lower.replace(keyword, "").strip()
            # Remove university name from topic
            for uni in ["ned", "iba", "uok", "ku", "fast", "nuces", "szabist", "dha suffa", "dsu", "dha", "duet", "dawood", "smiu"]:
                topic = topic.replace(uni, "").strip()
            
            if topic:
                # Construct search URL restricted to the university website
                search_query = topic.replace(" ", "+")
                search_url = f"https://www.google.com/search?q=site:{search_domain}+{search_query}"
                return True, search_url, f"{topic} (Search)", university_name
    
    return False, None, None, None

@app.get("/", response_class=HTMLResponse)
async def get():
    with open("index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("\n" + "=" * 50)
    print("Student connected via WebSocket")
    print("=" * 50)
    
    try:
        while True:
            # Receive text message
            message = await websocket.receive_text()
            try:
                data = json.loads(message)
                msg_type = data.get("type", "")
                
                if msg_type == "query":
                    user_text = data.get("text", "").strip()
                    if not user_text:
                        continue
                    
                    print(f"\nUser: {user_text}")
                    
                    is_nav, url, page_name, university_name = detect_navigation_request(user_text)
                    
                    if is_nav and url:
                        print(f"Navigation: Opening {university_name} - {page_name} -> {url}")
                        await websocket.send_json({
                            "type": "navigate",
                            "url": url,
                            "page_name": page_name,
                            "university": university_name
                        })
                        await websocket.send_json({
                            "type": "response",
                            "text": f"Opening the {page_name} page for {university_name}."
                        })
                        continue
                    
                    await websocket.send_json({
                        "type": "status",
                        "status": "processing",
                        "message": "Searching knowledge base..."
                    })
                    
                    try:
                        raw_response = get_groq_response(user_text)
                        clean_response = clean_text_for_tts(raw_response)
                        print(f"Assistant: {clean_response[:100]}...")
                        await websocket.send_json({
                            "type": "response",
                            "text": clean_response
                        })
                    except Exception as e:
                        print(f"RAG Error: {e}")
                        await websocket.send_json({
                            "type": "response",
                            "text": "I apologize, but I encountered an error while searching for information."
                        })
                
                elif msg_type == "ping":
                    await websocket.send_json({"type": "pong"})
                    
            except json.JSONDecodeError:
                continue
                
    except WebSocketDisconnect:
        print("Student disconnected")
    except Exception as e:
        print(f"WebSocket Error: {e}")
    finally:
        print("=" * 50 + "\n")

if __name__ == "__main__":
    import uvicorn
    
    # Check if vector database exists
    if not os.path.exists(DB_PATH):
        print("Creating vector database...")
        create_vector_db()
    
    # Get port from environment variable for Render
    port = int(os.environ.get("PORT", 8080))
    print(f"Starting server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
