#!/usr/bin/env python3
"""
Seed marketplace with blueprints from the marketplace directory.

This script loads YAML blueprints from blueprints/marketplace/ and adds them
to the database as public blueprints owned by a system user.

Usage:
    poetry run python scripts/seed_marketplace.py
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables
load_dotenv()

from sqlalchemy.orm import Session
from frankenagent.db.database import SessionLocal, engine
from frankenagent.db.models import Base, User, Blueprint
from frankenagent.config.loader import BlueprintLoader
from frankenagent.compiler.validator import BlueprintValidator
import yaml


def get_or_create_system_user(db: Session) -> User:
    """Get or create the system user for marketplace blueprints."""
    system_email = "marketplace@frankenagent.com"
    
    user = db.query(User).filter(User.email == system_email).first()
    
    if not user:
        print(f"Creating system user: {system_email}")
        user = User(
            email=system_email,
            full_name="FrankenAgent Marketplace",
            password_hash="",  # System user, no password
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"✅ Created system user: {user.id}")
    else:
        print(f"✅ Found existing system user: {user.id}")
    
    return user


def seed_blueprint(db: Session, user: User, yaml_path: Path) -> bool:
    """Seed a single blueprint from YAML file."""
    print(f"\n📋 Processing: {yaml_path.name}")
    
    try:
        # Load YAML
        with open(yaml_path, 'r') as f:
            blueprint_data = yaml.safe_load(f)
        
        name = blueprint_data.get('name', yaml_path.stem)
        description = blueprint_data.get('description', '')
        
        # Check if blueprint already exists
        existing = db.query(Blueprint).filter(
            Blueprint.user_id == user.id,
            Blueprint.name == name,
            Blueprint.is_deleted == False
        ).first()
        
        if existing:
            print(f"   ⚠️  Blueprint '{name}' already exists (ID: {existing.id})")
            
            # Update if needed
            if existing.blueprint_data != blueprint_data:
                print(f"   🔄 Updating blueprint data...")
                existing.blueprint_data = blueprint_data
                existing.description = description
                existing.version += 1
                db.commit()
                print(f"   ✅ Updated to version {existing.version}")
            else:
                print(f"   ✅ Already up to date")
            
            return True
        
        # Validate blueprint
        validator = BlueprintValidator()
        result = validator.validate(blueprint_data)
        
        if not result.valid:
            print(f"   ❌ Validation failed:")
            for error in result.errors:
                print(f"      - {error.field}: {error.message}")
            return False
        
        # Create new blueprint
        blueprint = Blueprint(
            user_id=user.id,
            name=name,
            description=description,
            blueprint_data=result.normalized_blueprint,
            version=1,
            is_public=True,  # Marketplace blueprints are public
            clone_count=0,
            rating_sum=0,
            rating_count=0
        )
        
        db.add(blueprint)
        db.commit()
        db.refresh(blueprint)
        
        print(f"   ✅ Created blueprint: {blueprint.id}")
        print(f"      Name: {name}")
        print(f"      Description: {description[:60]}...")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main seeding function."""
    print("=" * 80)
    print("  FrankenAgent Marketplace Seeder")
    print("=" * 80)
    
    # Create tables if they don't exist
    print("\n📊 Ensuring database tables exist...")
    Base.metadata.create_all(bind=engine)
    print("✅ Database ready")
    
    # Get database session
    db = SessionLocal()
    
    try:
        # Get or create system user
        print("\n👤 Setting up system user...")
        system_user = get_or_create_system_user(db)
        
        # Find all marketplace blueprints
        marketplace_dir = Path("blueprints/marketplace")
        
        if not marketplace_dir.exists():
            print(f"\n❌ Marketplace directory not found: {marketplace_dir}")
            return 1
        
        yaml_files = list(marketplace_dir.glob("*.yaml"))
        
        if not yaml_files:
            print(f"\n⚠️  No YAML files found in {marketplace_dir}")
            return 0
        
        print(f"\n📦 Found {len(yaml_files)} blueprint(s) to seed")
        
        # Seed each blueprint
        success_count = 0
        fail_count = 0
        
        for yaml_path in sorted(yaml_files):
            if seed_blueprint(db, system_user, yaml_path):
                success_count += 1
            else:
                fail_count += 1
        
        # Summary
        print("\n" + "=" * 80)
        print("  Summary")
        print("=" * 80)
        print(f"✅ Successful: {success_count}")
        if fail_count > 0:
            print(f"❌ Failed: {fail_count}")
        print(f"\n📊 Total marketplace blueprints: {success_count}")
        
        # List all public blueprints
        print("\n📋 Current marketplace listings:")
        blueprints = db.query(Blueprint).filter(
            Blueprint.is_public == True,
            Blueprint.is_deleted == False
        ).order_by(Blueprint.name).all()
        
        for i, bp in enumerate(blueprints, 1):
            execution_mode = bp.blueprint_data.get('legs', {}).get('execution_mode', 'single_agent')
            team_indicator = " 👥" if execution_mode == "team" else ""
            print(f"   {i}. {bp.name}{team_indicator}")
            print(f"      ID: {bp.id}")
            print(f"      Mode: {execution_mode}")
            print(f"      Clones: {bp.clone_count}, Ratings: {bp.rating_count}")
        
        print("\n✅ Marketplace seeding complete!")
        
        return 0 if fail_count == 0 else 1
        
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return 1
        
    finally:
        db.close()


if __name__ == "__main__":
    exit(main())
