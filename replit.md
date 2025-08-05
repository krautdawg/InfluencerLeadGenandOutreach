# Instagram LeadGen - Full-Stack Application

## Overview

K+L Influence is a Flask-based Instagram lead generation and outreach automation tool. It crawls Instagram hashtags, enriches profile data, and generates personalized email outreach campaigns. The application features a modern, professional design adhering to the K+L Internal Web App Style Guide, utilizing Natural Green branding, Inter typography, and Google Sheets-style table interactions for efficient data management. Its core purpose is to streamline influencer outreach by providing targeted leads and automated communication.

## User Preferences

Preferred communication style: Simple, everyday language. Before implementing any code changes, always lay out what code changes will be implemented and then let the user decide to approve, change, or deny the code changes. The user is happy to receive recommendations on how to improve the code. The user is happy to receive recommendations on how to improve the code.

## System Architecture

### Frontend Architecture
- **Framework**: Bootstrap 5 with custom CSS styling.
- **JavaScript**: Vanilla JavaScript for client-side interactions, including keyboard navigation, debounced filtering, and toast notifications.
- **Design Philosophy**: Modern, professional design following the K+L Internal Web App Style Guide (Natural Green branding, Inter typography).
- **UI/UX Decisions**:
    - Google Sheets-style tables with sticky headers, sticky username column, sorting, and inline editing.
    - Collapsible left navigation sidebar with persistent state.
    - Modal system for session configuration, email/prompt editing, and confirmations.
    - Responsive design for mobile and tablet devices, including auto-collapse sidebar and table card view.
    - Visual feedback for processing states (e.g., button disabling, progress bars, lead count updates).

### Backend Architecture
- **Framework**: Flask (Python web framework).
- **Database**: PostgreSQL with Flask-SQLAlchemy ORM for persistent data storage.
- **Models**: `Lead`, `Product`, `SystemPrompt`, `HashtagUsernamePair`, `ProcessingSession` for storing application data.
- **Concurrency**: `asyncio` and `httpx` for asynchronous operations, `ThreadPoolExecutor` for parallel API calls.
- **Session Management**: Flask sessions for maintaining user state and authentication.
- **Data Processing Pipeline**:
    1. **Hashtag Crawling**: Discovers Instagram hashtag variants and associated usernames.
    2. **Profile Enrichment**: Collects comprehensive Instagram profile data (followers, bio, full name, business status).
    3. **Contact Discovery**: Utilizes AI (Perplexity) to find missing contact information (email, phone, website).
    4. **Deduplication**: Removes duplicate profiles based on unique identifiers.
    5. **Email Generation**: Leverages OpenAI GPT-4o to create personalized German outreach emails, dynamically selecting prompts based on product assignment.
- **Anti-Scraping Strategy**: Implements batch processing with randomized and extended pauses to evade Instagram detection.
- **Resource Protection**: Mutual exclusion prevents simultaneous heavy operations (e.g., lead generation and email draft creation).
- **Authentication**: Basic login system with password protection using Replit secrets.
- **Logging**: Robust debug logging system for API calls, errors, and performance monitoring.

### Technical Implementations
- **Dynamic Prompt System**: Conditional template markup (`[IF variable_enabled]`) ensures AI prompts only include relevant information based on user selections.
- **Structured Data Generation**: Checkbox variables are passed as auto-generated structured data to OpenAI, simplifying prompt engineering.
- **Incremental Saves**: Leads are saved to the database incrementally after each batch to prevent data loss.
- **Client-Side Pagination**: Efficient client-side pagination for large datasets with configurable page sizes and persistent preferences.
- **Advanced Filtering**: Comprehensive table filtering including text search, numeric range filters with pre-set options, and date filtering with various presets.

## External Dependencies

### Core APIs
- **Apify**: For Instagram hashtag crawling (actor `DrF9mzPPEuVizVF4l`) and profile data enrichment (actor `8WEn9FvZnhE7lM3oA`).
- **Perplexity AI**: For contact information discovery and enrichment.
- **OpenAI GPT-4o**: For personalized email content generation.
- **Gmail API**: For sending outreach emails.

### Python Packages
- **Flask**: Web framework.
- **Flask-SQLAlchemy**: ORM for PostgreSQL database integration.
- **httpx**: Asynchronous HTTP client.
- **asyncio**: Asynchronous programming support.
- **google-auth**, **google-api-python-client**: For Google API authentication and Gmail client.
- **openai**: OpenAI API client.
- **python-dotenv**: For environment variable management.
- **psycopg2**: PostgreSQL adapter.

### Frontend Dependencies
- **Bootstrap 5**: UI framework and responsive design.
- **Font Awesome**: Icon library.
- **Google Fonts**: Specifically, the "Inter" font family for typography.

## Recent Changes

### 2025-08-05: TOTP Two-Factor Authentication Implementation (COMPLETED)
- **Feature**: Vollständige TOTP-basierte Zwei-Faktor-Authentifizierung mit Mandatory Setup für bestehende Benutzer
- **Sicherheitserweiterung**:
  - **TOTP Integration**: PyOTP-basierte Implementierung mit Google Authenticator-Kompatibilität
  - **QR-Code Setup**: Automatische QR-Code-Generierung für einfache Authenticator-App-Konfiguration
  - **Backup-Codes**: 10 einmalige Backup-Codes für Notfall-Zugang bei verlorenem Gerät
  - **Mandatory Activation**: Bestehende Benutzer müssen 2FA bei nächstem Login einrichten
- **Backend-Implementierung**:
  - **Erweiterte User-Model**: Neue Felder `two_factor_secret`, `two_factor_enabled`, `backup_codes`
  - **Mehrstufiger Login-Flow**: Username/Password → 2FA Setup/Verification → Dashboard-Zugang
  - **TOTP-Verifikation**: 30-Sekunden-Fenster mit 1-Periode-Toleranz für Zeitabweichungen
  - **Session-Management**: Temporäre Session-States für sichere Multi-Step-Authentifizierung
- **Frontend-Implementierung**:
  - **Setup-Seite**: Responsive QR-Code-Interface mit manueller Secret-Eingabe-Option
  - **Verifikations-Seite**: 6-stellige TOTP-Eingabe mit Backup-Code-Fallback
  - **Abschluss-Seite**: Backup-Code-Anzeige mit Copy-Funktion und Sicherheitshinweisen
  - **K+L Design**: Konsistente Natural Green-Farbgebung und Inter-Typografie
- **Sicherheitsfeatures**:
  - **Backup-Code-System**: JSON-gespeicherte, einmalig verwendbare 8-stellige Codes
  - **Session-Schutz**: Temporäre Anmeldedaten nur während 2FA-Flow verfügbar
  - **Auto-Format**: Client-seitige Eingabe-Validierung und -Formatierung
  - **Sichere Secret-Generierung**: Kryptographisch sichere TOTP-Secrets mit pyotp.random_base32()
- **Migration-Strategie**:
  - **Nahtlose Einführung**: Bestehende Benutzer können sich normal anmelden
  - **Mandatory Setup**: 2FA-Einrichtung wird bei nächstem Login erzwungen
  - **Backward-Kompatibilität**: Alte Sessions bleiben gültig bis zur nächsten Anmeldung
- **Abhängigkeiten**:
  - **PyOTP**: TOTP-Implementierung und Secret-Generierung
  - **QRCode**: QR-Code-Bildgenerierung für Authenticator-Apps
  - **Pillow**: Bildverarbeitung für QR-Code-Rendering
- **Status**: TOTP 2FA vollständig implementiert und für alle Benutzer aktiviert

### 2025-08-05: Legacy Login System Removal (COMPLETED)
- **Entfernung**: Standard Login (APP_PASSWORD) vollständig entfernt
- **Vereinfachung**: Nur noch Username-Password-Authentifizierung aktiv
- **Vorbereitung**: Login-System für 2FA-Integration optimiert
- **Session-Cleanup**: Legacy Session-Variablen entfernt
- **Status**: Single Login System implementiert

### 2025-08-03: Dual-Login System mit Rollenbasierter Zugriffskontrolle (SUPERSEDED)
- **Feature**: Implementierung eines vollständigen Mehrbenutzersystems mit separaten Admin- und Viewer-Zugängen
- **Sicherheitserweiterung**:
  - **Dual-Login-System**: K+L behält bisherigen APP_PASSWORD Login mit gleichen Rechten
  - **Admin-Login**: Neues benutzerkonto-basiertes System mit sicherer Passwort-Hashing (werkzeug.security)
  - **Rollenbasierte Kontrolle**: Admin (Vollzugriff) und Viewer (nur Leserechte) Rollen
- **Backend-Implementierung**:
  - **User-Model**: Neue User-Tabelle mit username, password_hash, role, created_at, last_login
  - **Authentication-Decorators**: `@login_required` (beide Systeme), `@admin_required` (nur User-System)
  - **Session-Management**: Erweitert um user_id, username, role für Benutzerverfolgung
  - **Migration-Safe**: Bestehende K+L-Funktionalität bleibt unverändert erhalten
- **Frontend-Erweiterungen**:
  - **Tab-basiertes Login**: "Standard Login" (K+L) und "Admin Login" mit animierten Übergängen
  - **Admin-Navigation**: Benutzerverwaltung-Button nur für Admin-Benutzer sichtbar
  - **User-Identifikation**: Logout-Button zeigt aktuellen Benutzer (Username oder "K+L")
- **Admin-Panel**:
  - **Benutzerverwaltung**: Vollständiges Interface zur Erstellung, Bearbeitung und Löschung von Benutzern
  - **Passwort-Reset**: Admin kann Benutzerpasswörter zurücksetzen
  - **Rollenverwaltung**: Visuelle Unterscheidung zwischen Admin- und Viewer-Rollen
  - **Sicherheitsfeatures**: Selbstlöschung-Schutz, Bestätigungsdialoge
- **Standard-Benutzer**:
  - **Default Admin**: Username "admin", Passwort "admin123" (beim ersten Start erstellt)
  - **Sofortige Verfügbarkeit**: System erstellt automatisch ersten Admin-Account
  - **Passwort-Änderung**: Admin sollte Standardpasswort sofort ändern
- **Backward-Kompatibilität**:
  - **K+L Workflow**: Unverändert - weiterhin APP_PASSWORD Login möglich
  - **Gleiche Rechte**: K+L behält Vollzugriff auf alle bisherigen Funktionen
  - **Nahtlose Koexistenz**: Beide Login-Systeme funktionieren parallel ohne Konflikte
- **Anwaltssichere Struktur**:
  - **Separate Zugänge**: K+L und Admin haben getrennte Anmeldedaten
  - **Audit-Trail**: Last_login Tracking für alle Benutzer
  - **Rollenbasierte Berechtigung**: Klare Trennung zwischen Admin- und Viewer-Rechten
- **Status**: Dual-Login-System vollständig implementiert und einsatzbereit
```