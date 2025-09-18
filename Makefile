# Makefile for Flask CMS
.PHONY: help build up down restart logs shell backup restore monitor clean test

# Default target
help: ## نمایش راهنمای دستورات
	@echo "Flask CMS - دستورات مفید:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Development commands
dev: ## اجرای سیستم در حالت development
	@echo "🚀 راه‌اندازی سیستم در حالت development..."
	docker-compose up -d
	@echo "✅ سیستم آماده است: http://localhost"

prod: ## اجرای سیستم در حالت production
	@echo "🚀 راه‌اندازی سیستم در حالت production..."
	docker-compose -f docker-compose.prod.yml up -d
	@echo "✅ سیستم آماده است: http://localhost"

# Build commands
build: ## ساخت imageهای Docker
	@echo "🔨 ساخت imageهای Docker..."
	docker-compose build --no-cache

build-prod: ## ساخت imageهای Docker برای production
	@echo "🔨 ساخت imageهای Docker برای production..."
	docker-compose -f docker-compose.prod.yml build --no-cache

# Container management
up: ## راه‌اندازی containerها
	@echo "🚀 راه‌اندازی containerها..."
	docker-compose up -d

down: ## متوقف کردن containerها
	@echo "⏹️ متوقف کردن containerها..."
	docker-compose down

restart: ## راه‌اندازی مجدد containerها
	@echo "🔄 راه‌اندازی مجدد containerها..."
	docker-compose restart

# Logs and monitoring
logs: ## مشاهده لاگ‌ها
	@echo "📝 نمایش لاگ‌ها..."
	docker-compose logs -f

logs-web: ## مشاهده لاگ‌های web
	@echo "📝 نمایش لاگ‌های web..."
	docker-compose logs -f web

logs-db: ## مشاهده لاگ‌های دیتابیس
	@echo "📝 نمایش لاگ‌های دیتابیس..."
	docker-compose logs -f db

monitor: ## مانیتورینگ سیستم
	@echo "📊 مانیتورینگ سیستم..."
	@./scripts/monitor.sh

# Database operations
backup: ## ایجاد بکاپ از دیتابیس
	@echo "💾 ایجاد بکاپ از دیتابیس..."
	@./scripts/backup.sh

restore: ## بازیابی دیتابیس (نیاز به نام فایل)
	@echo "🔄 بازیابی دیتابیس..."
	@if [ -z "$(FILE)" ]; then \
		echo "❌ لطفاً نام فایل بکاپ را مشخص کنید: make restore FILE=backup_file.sql.gz"; \
		exit 1; \
	fi
	@./scripts/restore.sh $(FILE)

# Shell access
shell: ## دسترسی به shell container اصلی
	@echo "🐚 دسترسی به shell..."
	docker-compose exec web bash

shell-db: ## دسترسی به shell دیتابیس
	@echo "🐚 دسترسی به shell دیتابیس..."
	docker-compose exec db bash

# Database management
db-shell: ## دسترسی به shell دیتابیس PostgreSQL
	@echo "🗄️ دسترسی به shell دیتابیس..."
	docker-compose exec db psql -U cms_user -d cms_db

db-init: ## راه‌اندازی اولیه دیتابیس
	@echo "🗄️ راه‌اندازی اولیه دیتابیس..."
	docker-compose exec web python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all(); print('✅ دیتابیس راه‌اندازی شد')"

# Testing
test: ## اجرای تست‌ها
	@echo "🧪 اجرای تست‌ها..."
	docker-compose exec web python -m pytest tests/ -v

# Security
security-check: ## بررسی امنیت
	@echo "🔒 بررسی امنیت..."
	@echo "بررسی فایل‌های حساس..."
	@if [ -f ".env" ]; then \
		echo "⚠️ فایل .env موجود است - مطمئن شوید که در .gitignore قرار دارد"; \
	else \
		echo "✅ فایل .env موجود نیست"; \
	fi
	@echo "بررسی SSL certificates..."
	@if [ -f "ssl/cert.pem" ] && [ -f "ssl/key.pem" ]; then \
		echo "✅ SSL certificates موجود است"; \
	else \
		echo "⚠️ SSL certificates موجود نیست - برای production نیاز است"; \
	fi

# Cleanup
clean: ## پاکسازی containerها و volumeها
	@echo "🧹 پاکسازی سیستم..."
	docker-compose down -v
	docker system prune -f
	@echo "✅ پاکسازی تکمیل شد"

clean-all: ## پاکسازی کامل (شامل imageها)
	@echo "🧹 پاکسازی کامل..."
	docker-compose down -v
	docker system prune -a -f
	@echo "✅ پاکسازی کامل تکمیل شد"

# Status
status: ## نمایش وضعیت سیستم
	@echo "📊 وضعیت سیستم:"
	@docker-compose ps
	@echo ""
	@echo "💾 استفاده از منابع:"
	@docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"

# Health check
health: ## بررسی سلامت سیستم
	@echo "🏥 بررسی سلامت سیستم..."
	@curl -f http://localhost/health || echo "❌ سیستم مشکل دارد"

# Quick setup
setup: ## راه‌اندازی سریع سیستم
	@echo "⚡ راه‌اندازی سریع سیستم..."
	@if [ ! -f ".env" ]; then \
		cp env.example .env; \
		echo "📋 فایل .env ایجاد شد - لطفاً آن را ویرایش کنید"; \
	fi
	@make build
	@make up
	@echo "✅ سیستم آماده است: http://localhost"











