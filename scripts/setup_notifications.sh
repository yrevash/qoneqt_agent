#!/bin/bash

# ============================================================================
# Qoneqt Email Notification Setup Script
# ============================================================================
# This script helps you quickly configure email notifications

set -e

echo "============================================"
echo "  📧 Qoneqt Email Notification Setup"
echo "============================================"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from example..."
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "✅ Created .env file. Please edit it with your details."
    else
        echo "❌ .env.example not found. Please create .env manually."
        exit 1
    fi
fi

echo "Please provide your email configuration:"
echo ""

# Get email provider choice
echo "Select your email provider:"
echo "1) Gmail (recommended for personal use)"
echo "2) Outlook/Hotmail"
echo "3) Yahoo Mail"
echo "4) Other (custom SMTP)"
read -p "Enter choice (1-4): " provider_choice

case $provider_choice in
    1)
        SMTP_HOST="smtp.gmail.com"
        SMTP_PORT=587
        echo ""
        echo "📧 Gmail Setup:"
        echo "You need to generate an App Password (NOT your regular password)"
        echo "1. Go to: https://myaccount.google.com/apppasswords"
        echo "2. Sign in to your Google account"
        echo "3. Click 'Select app' → Choose 'Mail'"
        echo "4. Click 'Select device' → Choose 'Other' → Type 'Qoneqt'"
        echo "5. Click 'Generate'"
        echo "6. Copy the 16-character password"
        echo ""
        ;;
    2)
        SMTP_HOST="smtp-mail.outlook.com"
        SMTP_PORT=587
        ;;
    3)
        SMTP_HOST="smtp.mail.yahoo.com"
        SMTP_PORT=587
        echo ""
        echo "📧 Yahoo Mail Setup:"
        echo "You need to generate an App Password"
        echo "Go to: https://login.yahoo.com/account/security"
        echo ""
        ;;
    4)
        read -p "Enter SMTP host (e.g., smtp.yourcompany.com): " SMTP_HOST
        read -p "Enter SMTP port (usually 587 or 465): " SMTP_PORT
        ;;
    *)
        echo "Invalid choice. Exiting."
        exit 1
        ;;
esac

# Get email and password
read -p "Enter your email address: " EMAIL_ADDRESS
read -sp "Enter your SMTP password (or app password): " EMAIL_PASSWORD
echo ""
read -p "Where should alerts be sent? (press Enter to use same email): " ALERT_EMAIL
if [ -z "$ALERT_EMAIL" ]; then
    ALERT_EMAIL=$EMAIL_ADDRESS
fi

echo ""
echo "Updating configuration files..."

# Update .env file
if grep -q "^SMTP_HOST=" .env; then
    sed -i "s|^SMTP_HOST=.*|SMTP_HOST=$SMTP_HOST|" .env
    sed -i "s|^SMTP_PORT=.*|SMTP_PORT=$SMTP_PORT|" .env
    sed -i "s|^SMTP_USER=.*|SMTP_USER=$EMAIL_ADDRESS|" .env
    sed -i "s|^SMTP_PASSWORD=.*|SMTP_PASSWORD=$EMAIL_PASSWORD|" .env
else
    echo "" >> .env
    echo "# Email Notification Settings" >> .env
    echo "SMTP_HOST=$SMTP_HOST" >> .env
    echo "SMTP_PORT=$SMTP_PORT" >> .env
    echo "SMTP_USER=$EMAIL_ADDRESS" >> .env
    echo "SMTP_PASSWORD=$EMAIL_PASSWORD" >> .env
fi

# Update alertmanager config
sed -i "s|smtp_smarthost:.*|smtp_smarthost: '$SMTP_HOST:$SMTP_PORT'|" infra/alertmanager/config.yml
sed -i "s|smtp_from:.*|smtp_from: '$EMAIL_ADDRESS'|" infra/alertmanager/config.yml
sed -i "s|smtp_auth_username:.*|smtp_auth_username: '$EMAIL_ADDRESS'|" infra/alertmanager/config.yml
sed -i "s|smtp_auth_password:.*|smtp_auth_password: '$EMAIL_PASSWORD'|" infra/alertmanager/config.yml

# Update alert recipients
sed -i "s|to: 'your-email@gmail.com'|to: '$ALERT_EMAIL'|g" infra/alertmanager/config.yml

echo ""
echo "✅ Configuration updated!"
echo ""
echo "Next steps:"
echo "1. Restart services: docker-compose restart alertmanager api"
echo "2. Test notifications: docker-compose stop worker"
echo "3. Check your email in 30 seconds"
echo "4. Start worker again: docker-compose start worker"
echo ""
echo "📚 For more details, see NOTIFICATION_SETUP.md"
echo ""
