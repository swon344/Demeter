from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime, UTC
from flask_debugtoolbar import DebugToolbarExtension

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///demeter.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['DEBUG'] = True
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
toolbar = DebugToolbarExtension(app)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'admin_login'


# Veritabanı modelleri (ORM)
# Taksonomi modelleri
class TaxonomyDomain(db.Model):
    __tablename__ = 'taxonomy_domain'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now(UTC))
    kingdoms = db.relationship('TaxonomyKingdom', backref='domain', lazy=True)


class TaxonomyKingdom(db.Model):
    __tablename__ = 'taxonomy_kingdom'
    id = db.Column(db.Integer, primary_key=True)
    domain_id = db.Column(db.Integer, db.ForeignKey('taxonomy_domain.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now(UTC))
    phyla = db.relationship('TaxonomyPhylum', backref='kingdom', lazy=True)
    __table_args__ = (db.UniqueConstraint('domain_id', 'name'),)


class TaxonomyPhylum(db.Model):
    __tablename__ = 'taxonomy_phylum'
    id = db.Column(db.Integer, primary_key=True)
    kingdom_id = db.Column(db.Integer, db.ForeignKey('taxonomy_kingdom.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now(UTC))
    classes = db.relationship('TaxonomyClass', backref='phylum', lazy=True)
    __table_args__ = (db.UniqueConstraint('kingdom_id', 'name'),)


class TaxonomyClass(db.Model):
    __tablename__ = 'taxonomy_class'
    id = db.Column(db.Integer, primary_key=True)
    phylum_id = db.Column(db.Integer, db.ForeignKey('taxonomy_phylum.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now(UTC))
    orders = db.relationship('TaxonomyOrder', backref='class_', lazy=True)
    __table_args__ = (db.UniqueConstraint('phylum_id', 'name'),)


class TaxonomyOrder(db.Model):
    __tablename__ = 'taxonomy_order'
    id = db.Column(db.Integer, primary_key=True)
    class_id = db.Column(db.Integer, db.ForeignKey('taxonomy_class.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now(UTC))
    families = db.relationship('TaxonomyFamily', backref='order', lazy=True)
    __table_args__ = (db.UniqueConstraint('class_id', 'name'),)


class TaxonomyFamily(db.Model):
    __tablename__ = 'taxonomy_family'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('taxonomy_order.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now(UTC))
    genera = db.relationship('TaxonomyGenus', backref='family', lazy=True)
    __table_args__ = (db.UniqueConstraint('order_id', 'name'),)


class TaxonomyGenus(db.Model):
    __tablename__ = 'taxonomy_genus'
    id = db.Column(db.Integer, primary_key=True)
    family_id = db.Column(db.Integer, db.ForeignKey('taxonomy_family.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now(UTC))
    __table_args__ = (db.UniqueConstraint('family_id', 'name'),)


class Seed(db.Model):
    __tablename__ = 'seeds'
    id = db.Column(db.Integer, primary_key=True)
    genus_id = db.Column(db.Integer, db.ForeignKey('taxonomy_genus.id'), nullable=False)
    species_name = db.Column(db.String(100), nullable=False)
    full_scientific_name = db.Column(db.String(200), nullable=False)
    common_name = db.Column(db.String(100))
    icon = db.Column(db.String(50))
    description = db.Column(db.Text)
    growth_time = db.Column(db.Integer)
    water_req = db.Column(db.Float)
    light_req = db.Column(db.Float)
    nutrient_req = db.Column(db.Float)
    oxygen_production = db.Column(db.Float)
    biomass_production = db.Column(db.Float)
    tier = db.Column(db.Integer, default=1)
    is_unlocked = db.Column(db.Boolean, default=False)
    mutation_chance = db.Column(db.Float, default=0.1)
    created_at = db.Column(db.DateTime, default=datetime.now(UTC))

    genus = db.relationship('TaxonomyGenus', backref='seeds')
    traits = db.relationship('SeedTrait', secondary='seed_trait_relations', backref='seeds')

    __table_args__ = (db.UniqueConstraint('genus_id', 'species_name'),)


class SeedTrait(db.Model):
    __tablename__ = 'seed_traits'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    effect_type = db.Column(db.String(50))
    effect_value = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.now(UTC))


class SeedTraitRelation(db.Model):
    __tablename__ = 'seed_trait_relations'
    seed_id = db.Column(db.Integer, db.ForeignKey('seeds.id'), primary_key=True)
    trait_id = db.Column(db.Integer, db.ForeignKey('seed_traits.id'), primary_key=True)


class SeedMutation(db.Model):
    __tablename__ = 'seed_mutations'
    parent_seed_id = db.Column(db.Integer, db.ForeignKey('seeds.id'), primary_key=True)
    result_seed_id = db.Column(db.Integer, db.ForeignKey('seeds.id'), primary_key=True)
    probability = db.Column(db.Float, default=0.1)

    parent_seed = db.relationship('Seed', foreign_keys=[parent_seed_id], backref='mutations_as_parent')
    result_seed = db.relationship('Seed', foreign_keys=[result_seed_id], backref='mutations_as_result')


class AdminUser(UserMixin, db.Model):
    __tablename__ = 'admin_users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(100), unique=True)
    is_active = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.now(UTC))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


@login_manager.user_loader
def load_user(user_id):
    return AdminUser.query.get(int(user_id))


# Admin paneli rotaları
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if current_user.is_authenticated:
        return redirect(url_for('admin_dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = AdminUser.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            user.last_login = datetime.now(UTC)
            db.session.commit()
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Geçersiz kullanıcı adı veya şifre', 'error')

    return render_template('admin/login.html')


@app.route('/admin/logout')
@login_required
def admin_logout():
    logout_user()
    return redirect(url_for('admin_login'))


@app.route('/admin')
@login_required
def admin_dashboard():
    seed_count = Seed.query.count()
    domain_count = TaxonomyDomain.query.count()
    trait_count = SeedTrait.query.count()

    return render_template('admin/dashboard.html',
                           seed_count=seed_count,
                           domain_count=domain_count,
                           trait_count=trait_count)


# Taksonomi yönetim rotaları
@app.route('/admin/taxonomy/<level>')
@login_required
def admin_taxonomy(level):
    if level == 'domain':
        items = TaxonomyDomain.query.all()
        parent_items = None
    elif level == 'kingdom':
        items = TaxonomyKingdom.query.all()
        parent_items = TaxonomyDomain.query.all()
    elif level == 'phylum':
        items = TaxonomyPhylum.query.all()
        parent_items = TaxonomyKingdom.query.all()
    elif level == 'class':
        items = TaxonomyClass.query.all()
        parent_items = TaxonomyPhylum.query.all()
    elif level == 'order':
        items = TaxonomyOrder.query.all()
        parent_items = TaxonomyClass.query.all()
    elif level == 'family':
        items = TaxonomyFamily.query.all()
        parent_items = TaxonomyOrder.query.all()
    elif level == 'genus':
        items = TaxonomyGenus.query.all()
        parent_items = TaxonomyFamily.query.all()
    else:
        flash('Geçersiz taksonomi seviyesi', 'error')
        return redirect(url_for('admin_dashboard'))

    return render_template(f'admin/taxonomy_{level}.html', items=items, parent_items=parent_items)


@app.route('/admin/taxonomy/<level>/add', methods=['GET', 'POST'])
@login_required
def admin_taxonomy_add(level):
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')

        if level == 'domain':
            item = TaxonomyDomain(name=name, description=description)
        elif level == 'kingdom':
            domain_id = request.form.get('domain_id')
            item = TaxonomyKingdom(name=name, description=description, domain_id=domain_id)
        elif level == 'phylum':
            kingdom_id = request.form.get('kingdom_id')
            item = TaxonomyPhylum(name=name, description=description, kingdom_id=kingdom_id)
        elif level == 'class':
            phylum_id = request.form.get('phylum_id')
            item = TaxonomyClass(name=name, description=description, phylum_id=phylum_id)
        elif level == 'order':
            class_id = request.form.get('class_id')
            item = TaxonomyOrder(name=name, description=description, class_id=class_id)
        elif level == 'family':
            order_id = request.form.get('order_id')
            item = TaxonomyFamily(name=name, description=description, order_id=order_id)
        elif level == 'genus':
            family_id = request.form.get('family_id')
            item = TaxonomyGenus(name=name, description=description, family_id=family_id)
        else:
            flash('Geçersiz taksonomi seviyesi', 'error')
            return redirect(url_for('admin_dashboard'))

        try:
            db.session.add(item)
            db.session.commit()
            flash(f'{level.capitalize()} başarıyla eklendi', 'success')
            return redirect(url_for('admin_taxonomy', level=level))
        except Exception as e:
            db.session.rollback()
            flash(f'Hata: {str(e)}', 'error')

    # GET isteği için form sayfasını göster
    if level == 'domain':
        parent_items = None
    elif level == 'kingdom':
        parent_items = TaxonomyDomain.query.all()
    elif level == 'phylum':
        parent_items = TaxonomyKingdom.query.all()
    elif level == 'class':
        parent_items = TaxonomyPhylum.query.all()
    elif level == 'order':
        parent_items = TaxonomyClass.query.all()
    elif level == 'family':
        parent_items = TaxonomyOrder.query.all()
    elif level == 'genus':
        parent_items = TaxonomyFamily.query.all()
    else:
        flash('Geçersiz taksonomi seviyesi', 'error')
        return redirect(url_for('admin_dashboard'))

    return render_template(f'admin/taxonomy_{level}_form.html', parent_items=parent_items)


@app.route('/admin/taxonomy/<level>/edit/<int:item_id>', methods=['GET', 'POST'])
@login_required
def admin_taxonomy_edit(level, item_id):
    # İlgili taksonomi seviyesine göre öğeyi al
    if level == 'domain':
        item = TaxonomyDomain.query.get_or_404(item_id)
        parent_items = None
    elif level == 'kingdom':
        item = TaxonomyKingdom.query.get_or_404(item_id)
        parent_items = TaxonomyDomain.query.all()
    elif level == 'phylum':
        item = TaxonomyPhylum.query.get_or_404(item_id)
        parent_items = TaxonomyKingdom.query.all()
    elif level == 'class':
        item = TaxonomyClass.query.get_or_404(item_id)
        parent_items = TaxonomyPhylum.query.all()
    elif level == 'order':
        item = TaxonomyOrder.query.get_or_404(item_id)
        parent_items = TaxonomyClass.query.all()
    elif level == 'family':
        item = TaxonomyFamily.query.get_or_404(item_id)
        parent_items = TaxonomyOrder.query.all()
    elif level == 'genus':
        item = TaxonomyGenus.query.get_or_404(item_id)
        parent_items = TaxonomyFamily.query.all()
    else:
        flash('Geçersiz taksonomi seviyesi', 'error')
        return redirect(url_for('admin_dashboard'))

    if request.method == 'POST':
        item.name = request.form.get('name')
        item.description = request.form.get('description')

        # Üst taksonomi seviyesi ilişkisini güncelle
        if level != 'domain':
            if level == 'kingdom':
                item.domain_id = request.form.get('domain_id')
            elif level == 'phylum':
                item.kingdom_id = request.form.get('kingdom_id')
            elif level == 'class':
                item.phylum_id = request.form.get('phylum_id')
            elif level == 'order':
                item.class_id = request.form.get('class_id')
            elif level == 'family':
                item.order_id = request.form.get('order_id')
            elif level == 'genus':
                item.family_id = request.form.get('family_id')

        try:
            db.session.commit()
            flash(f'{level.capitalize()} başarıyla güncellendi', 'success')
            return redirect(url_for('admin_taxonomy', level=level))
        except Exception as e:
            db.session.rollback()
            flash(f'Hata: {str(e)}', 'error')

    return render_template(f'admin/taxonomy_{level}_form.html', item=item, parent_items=parent_items, edit_mode=True)


@app.route('/admin/taxonomy/<level>/delete/<int:item_id>', methods=['POST'])
@login_required
def admin_taxonomy_delete(level, item_id):
    # İlgili taksonomi seviyesine göre öğeyi al
    if level == 'domain':
        item = TaxonomyDomain.query.get_or_404(item_id)
    elif level == 'kingdom':
        item = TaxonomyKingdom.query.get_or_404(item_id)
    elif level == 'phylum':
        item = TaxonomyPhylum.query.get_or_404(item_id)
    elif level == 'class':
        item = TaxonomyClass.query.get_or_404(item_id)
    elif level == 'order':
        item = TaxonomyOrder.query.get_or_404(item_id)
    elif level == 'family':
        item = TaxonomyFamily.query.get_or_404(item_id)
    elif level == 'genus':
        item = TaxonomyGenus.query.get_or_404(item_id)
    else:
        flash('Geçersiz taksonomi seviyesi', 'error')
        return redirect(url_for('admin_dashboard'))

    try:
        db.session.delete(item)
        db.session.commit()
        flash(f'{level.capitalize()} başarıyla silindi', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Hata: {str(e)}', 'error')

    return redirect(url_for('admin_taxonomy', level=level))


# Tohum yönetim rotaları
@app.route('/admin/seeds')
@login_required
def admin_seeds():
    seeds = Seed.query.all()
    return render_template('admin/seeds.html', seeds=seeds)


@app.route('/admin/seeds/add', methods=['GET', 'POST'])
@login_required
def admin_seed_add():
    if request.method == 'POST':
        # Form verilerini al
        genus_id = request.form.get('genus_id')
        species_name = request.form.get('species_name')
        common_name = request.form.get('common_name')
        icon = request.form.get('icon')
        description = request.form.get('description')
        growth_time = request.form.get('growth_time')
        water_req = request.form.get('water_req')
        light_req = request.form.get('light_req')
        nutrient_req = request.form.get('nutrient_req')
        oxygen_production = request.form.get('oxygen_production')
        biomass_production = request.form.get('biomass_production')
        tier = request.form.get('tier')
        is_unlocked = 'is_unlocked' in request.form
        mutation_chance = request.form.get('mutation_chance')

        # Genus'u al
        genus = TaxonomyGenus.query.get(genus_id)
        if not genus:
            flash('Geçersiz cins seçildi', 'error')
            return redirect(url_for('admin_seed_add'))

        # Bilimsel adı oluştur
        full_scientific_name = f"{genus.name} {species_name}"

        # Yeni tohum oluştur
        seed = Seed(
            genus_id=genus_id,
            species_name=species_name,
            full_scientific_name=full_scientific_name,
            common_name=common_name,
            icon=icon,
            description=description,
            growth_time=growth_time,
            water_req=water_req,
            light_req=light_req,
            nutrient_req=nutrient_req,
            oxygen_production=oxygen_production,
            biomass_production=biomass_production,
            tier=tier,
            is_unlocked=is_unlocked,
            mutation_chance=mutation_chance
        )

        try:
            db.session.add(seed)
            db.session.commit()

            # Özellikleri ekle
            trait_ids = request.form.getlist('traits')
            for trait_id in trait_ids:
                relation = SeedTraitRelation(seed_id=seed.id, trait_id=trait_id)
                db.session.add(relation)

            db.session.commit()
            flash('Tohum başarıyla eklendi', 'success')
            return redirect(url_for('admin_seeds'))
        except Exception as e:
            db.session.rollback()
            flash(f'Hata: {str(e)}', 'error')

    # GET isteği için form sayfasını göster
    genera = TaxonomyGenus.query.all()
    traits = SeedTrait.query.all()
    return render_template('admin/seed_form.html', genera=genera, traits=traits)


@app.route('/admin/seeds/edit/<int:seed_id>', methods=['GET', 'POST'])
@login_required
def admin_seed_edit(seed_id):
    seed = Seed.query.get_or_404(seed_id)

    if request.method == 'POST':
        # Form verilerini al
        genus_id = request.form.get('genus_id')
        species_name = request.form.get('species_name')
        common_name = request.form.get('common_name')
        icon = request.form.get('icon')
        description = request.form.get('description')
        growth_time = request.form.get('growth_time')
        water_req = request.form.get('water_req')
        light_req = request.form.get('light_req')
        nutrient_req = request.form.get('nutrient_req')
        oxygen_production = request.form.get('oxygen_production')
        biomass_production = request.form.get('biomass_production')
        tier = request.form.get('tier')
        is_unlocked = 'is_unlocked' in request.form
        mutation_chance = request.form.get('mutation_chance')

        # Genus'u al
        genus = TaxonomyGenus.query.get(genus_id)
        if not genus:
            flash('Geçersiz cins seçildi', 'error')
            return redirect(url_for('admin_seed_edit', seed_id=seed_id))

        # Bilimsel adı oluştur
        full_scientific_name = f"{genus.name} {species_name}"

        # Tohumu güncelle
        seed.genus_id = genus_id
        seed.species_name = species_name
        seed.full_scientific_name = full_scientific_name
        seed.common_name = common_name
        seed.icon = icon
        seed.description = description
        seed.growth_time = growth_time
        seed.water_req = water_req
        seed.light_req = light_req
        seed.nutrient_req = nutrient_req
        seed.oxygen_production = oxygen_production
        seed.biomass_production = biomass_production
        seed.tier = tier
        seed.is_unlocked = is_unlocked
        seed.mutation_chance = mutation_chance

        try:
            # Mevcut özellikleri temizle
            SeedTraitRelation.query.filter_by(seed_id=seed.id).delete()

            # Yeni özellikleri ekle
            trait_ids = request.form.getlist('traits')
            for trait_id in trait_ids:
                relation = SeedTraitRelation(seed_id=seed.id, trait_id=trait_id)
                db.session.add(relation)

            db.session.commit()
            flash('Tohum başarıyla güncellendi', 'success')
            return redirect(url_for('admin_seeds'))
        except Exception as e:
            db.session.rollback()
            flash(f'Hata: {str(e)}', 'error')

    # GET isteği için form sayfasını göster
    genera = TaxonomyGenus.query.all()
    traits = SeedTrait.query.all()

    # Tohumun mevcut özelliklerini al
    seed_traits = [relation.trait_id for relation in SeedTraitRelation.query.filter_by(seed_id=seed.id).all()]

    return render_template('admin/seed_form.html', seed=seed, genera=genera, traits=traits,
                           seed_traits=seed_traits, edit_mode=True)


@app.route('/admin/seeds/delete/<int:seed_id>', methods=['POST'])
@login_required
def admin_seed_delete(seed_id):
    seed = Seed.query.get_or_404(seed_id)

    try:
        # İlişkili kayıtları temizle
        SeedTraitRelation.query.filter_by(seed_id=seed.id).delete()
        SeedMutation.query.filter((SeedMutation.parent_seed_id == seed.id) |
                                  (SeedMutation.result_seed_id == seed.id)).delete()

        # Tohumu sil
        db.session.delete(seed)
        db.session.commit()
        flash('Tohum başarıyla silindi', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Hata: {str(e)}', 'error')

    return redirect(url_for('admin_seeds'))


# Tohum özellikleri yönetim rotaları
@app.route('/admin/seed_traits')
@login_required
def admin_seed_traits():
    traits = SeedTrait.query.all()
    return render_template('admin/seed_traits.html', traits=traits)


@app.route('/admin/seed_traits/add', methods=['GET', 'POST'])
@login_required
def admin_seed_trait_add():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        effect_type = request.form.get('effect_type')
        effect_value = request.form.get('effect_value')

        trait = SeedTrait(
            name=name,
            description=description,
            effect_type=effect_type,
            effect_value=effect_value
        )

        try:
            db.session.add(trait)
            db.session.commit()
            flash('Özellik başarıyla eklendi', 'success')
            return redirect(url_for('admin_seed_traits'))
        except Exception as e:
            db.session.rollback()
            flash(f'Hata: {str(e)}', 'error')

    return render_template('admin/seed_trait_form.html')


@app.route('/admin/seed_traits/edit/<int:trait_id>', methods=['GET', 'POST'])
@login_required
def admin_seed_trait_edit(trait_id):
    trait = SeedTrait.query.get_or_404(trait_id)

    if request.method == 'POST':
        trait.name = request.form.get('name')
        trait.description = request.form.get('description')
        trait.effect_type = request.form.get('effect_type')
        trait.effect_value = request.form.get('effect_value')

        try:
            db.session.commit()
            flash('Özellik başarıyla güncellendi', 'success')
            return redirect(url_for('admin_seed_traits'))
        except Exception as e:
            db.session.rollback()
            flash(f'Hata: {str(e)}', 'error')

    return render_template('admin/seed_trait_form.html', trait=trait, edit_mode=True)


@app.route('/admin/seed_traits/delete/<int:trait_id>', methods=['POST'])
@login_required
def admin_seed_trait_delete(trait_id):
    trait = SeedTrait.query.get_or_404(trait_id)

    try:
        # İlişkili kayıtları temizle
        SeedTraitRelation.query.filter_by(trait_id=trait.id).delete()

        # Özelliği sil
        db.session.delete(trait)
        db.session.commit()
        flash('Özellik başarıyla silindi', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Hata: {str(e)}', 'error')

    return redirect(url_for('admin_seed_traits'))


# Mutasyon yönetim rotaları
@app.route('/admin/mutations')
@login_required
def admin_mutations():
    mutations = db.session.query(
        SeedMutation,
        Seed.common_name.label('parent_name'),
        Seed.icon.label('parent_icon'),
        Seed.full_scientific_name.label('parent_scientific_name'),
        db.literal_column('second_seed.common_name').label('result_name'),
        db.literal_column('second_seed.icon').label('result_icon'),
        db.literal_column('second_seed.full_scientific_name').label('result_scientific_name')
    ).join(
        Seed, Seed.id == SeedMutation.parent_seed_id
    ).join(
        Seed, Seed.id == SeedMutation.result_seed_id, aliased=True, from_joinpoint=True
    ).all()

    return render_template('admin/mutations.html', mutations=mutations)


@app.route('/admin/mutations/add', methods=['GET', 'POST'])
@login_required
def admin_mutation_add():
    if request.method == 'POST':
        parent_seed_id = request.form.get('parent_seed_id')
        result_seed_id = request.form.get('result_seed_id')
        probability = request.form.get('probability')

        # Aynı tohum kontrolü
        if parent_seed_id == result_seed_id:
            flash('Ebeveyn ve sonuç tohumu aynı olamaz', 'error')
            seeds = Seed.query.all()
            return render_template('admin/mutation_form.html', seeds=seeds)

        # Mevcut mutasyon kontrolü
        existing = SeedMutation.query.filter_by(
            parent_seed_id=parent_seed_id,
            result_seed_id=result_seed_id
        ).first()

        if existing:
            flash('Bu mutasyon zaten tanımlanmış', 'error')
            seeds = Seed.query.all()
            return render_template('admin/mutation_form.html', seeds=seeds)

        mutation = SeedMutation(
            parent_seed_id=parent_seed_id,
            result_seed_id=result_seed_id,
            probability=probability
        )

        try:
            db.session.add(mutation)
            db.session.commit()
            flash('Mutasyon başarıyla eklendi', 'success')
            return redirect(url_for('admin_mutations'))
        except Exception as e:
            db.session.rollback()
            flash(f'Hata: {str(e)}', 'error')

    seeds = Seed.query.all()
    return render_template('admin/mutation_form.html', seeds=seeds)


@app.route('/admin/mutations/edit/<int:parent_id>/<int:result_id>', methods=['GET', 'POST'])
@login_required
def admin_mutation_edit(parent_id, result_id):
    mutation = SeedMutation.query.filter_by(
        parent_seed_id=parent_id,
        result_seed_id=result_id
    ).first_or_404()

    if request.method == 'POST':
        new_parent_id = request.form.get('parent_seed_id')
        new_result_id = request.form.get('result_seed_id')
        probability = request.form.get('probability')

        # Aynı tohum kontrolü
        if new_parent_id == new_result_id:
            flash('Ebeveyn ve sonuç tohumu aynı olamaz', 'error')
            seeds = Seed.query.all()
            return render_template('admin/mutation_form.html', mutation=mutation, seeds=seeds, edit_mode=True)

        # Mevcut mutasyon kontrolü (kendisi hariç)
        if new_parent_id != parent_id or new_result_id != result_id:
            existing = SeedMutation.query.filter_by(
                parent_seed_id=new_parent_id,
                result_seed_id=new_result_id
            ).first()

            if existing:
                flash('Bu mutasyon zaten tanımlanmış', 'error')
                seeds = Seed.query.all()
                return render_template('admin/mutation_form.html', mutation=mutation, seeds=seeds, edit_mode=True)

        # Eski mutasyonu sil
        db.session.delete(mutation)

        # Yeni mutasyon oluştur
        new_mutation = SeedMutation(
            parent_seed_id=new_parent_id,
            result_seed_id=new_result_id,
            probability=probability
        )

        try:
            db.session.add(new_mutation)
            db.session.commit()
            flash('Mutasyon başarıyla güncellendi', 'success')
            return redirect(url_for('admin_mutations'))
        except Exception as e:
            db.session.rollback()
            flash(f'Hata: {str(e)}', 'error')

    seeds = Seed.query.all()
    return render_template('admin/mutation_form.html', mutation=mutation, seeds=seeds, edit_mode=True)


@app.route('/admin/mutations/delete/<int:parent_id>/<int:result_id>', methods=['POST'])
@login_required
def admin_mutation_delete(parent_id, result_id):
    mutation = SeedMutation.query.filter_by(
        parent_seed_id=parent_id,
        result_seed_id=result_id
    ).first_or_404()

    try:
        db.session.delete(mutation)
        db.session.commit()
        flash('Mutasyon başarıyla silindi', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Hata: {str(e)}', 'error')

    return redirect(url_for('admin_mutations'))


# Oyun API'leri
@app.route('/api/seeds')
def api_seeds():
    # Oyuncunun açtığı tohumları getir
    if 'player_data' in session and 'unlocked_seeds' in session['player_data']:
        unlocked_seed_ids = session['player_data']['unlocked_seeds']
        seeds = Seed.query.filter(Seed.id.in_(unlocked_seed_ids)).all()
    else:
        # Sadece başlangıçta açık olan tohumları getir
        seeds = Seed.query.filter_by(is_unlocked=True).all()

    seed_list = []
    for seed in seeds:
        # Cins ve üst taksonomi bilgilerini al
        genus = seed.genus
        family = genus.family
        order = family.order
        class_ = order.class_
        phylum = class_.phylum
        kingdom = phylum.kingdom
        domain = kingdom.domain

        # Özellikleri al
        traits = [{"id": t.id, "name": t.name, "description": t.description} for t in seed.traits]

        seed_data = {
            "id": seed.id,
            "scientific_name": seed.full_scientific_name,
            "common_name": seed.common_name,
            "icon": seed.icon,
            "description": seed.description,
            "taxonomy": {
                "domain": {"id": domain.id, "name": domain.name},
                "kingdom": {"id": kingdom.id, "name": kingdom.name},
                "phylum": {"id": phylum.id, "name": phylum.name},
                "class": {"id": class_.id, "name": class_.name},
                "order": {"id": order.id, "name": order.name},
                "family": {"id": family.id, "name": family.name},
                "genus": {"id": genus.id, "name": genus.name},
                "species": seed.species_name
            },
            "growth_time": seed.growth_time,
            "requirements": {
                "water": seed.water_req,
                "light": seed.light_req,
                "nutrients": seed.nutrient_req
            },
            "production": {
                "oxygen": seed.oxygen_production,
                "biomass": seed.biomass_production
            },
            "tier": seed.tier,
            "traits": traits,
            "mutation_chance": seed.mutation_chance
        }
        seed_list.append(seed_data)

    return jsonify(seed_list)

@app.route('/api/update_resources', methods=['POST'])
def api_update_resources():
    if 'player_data' not in session:
        return jsonify({"success": False, "message": "Oyuncu verisi bulunamadı"})

    data = request.json

    # Kaynakları güncelle
    session['player_data']['resources'] = data
    session.modified = True

    return jsonify({"success": True})

# Yeni API endpoint'leri ekleyelim
@app.route('/api/update_crew', methods=['POST'])
def api_update_crew():
    if 'player_data' not in session:
        return jsonify({"success": False, "message": "Oyuncu verisi bulunamadı"})

    data = request.json

    # Mürettebat verilerini güncelle
    session['player_data']['crew'] = data
    session.modified = True

    return jsonify({"success": True})

@app.route('/api/advance_day', methods=['POST'])
def api_advance_day():
    if 'player_data' not in session:
        return jsonify({"success": False, "message": "Oyuncu verisi bulunamadı"})

    # Günü ilerlet
    session['player_data']['day'] += 1

    # Efor puanlarını yenile
    session['player_data']['crew']['effort_points'] = 100

    # Diğer günlük güncellemeler...

    session.modified = True

    return jsonify({
        "success": True,
        "day": session['player_data']['day'],
        "message": f"Gün {session['player_data']['day']} başladı!"
    })

@app.route('/api/taxonomy')
def api_taxonomy():
    # Tüm taksonomi verilerini getir
    domains = TaxonomyDomain.query.all()

    taxonomy_data = []
    for domain in domains:
        domain_data = {
            "id": domain.id,
            "name": domain.name,
            "description": domain.description,
            "kingdoms": []
        }

        for kingdom in domain.kingdoms:
            kingdom_data = {
                "id": kingdom.id,
                "name": kingdom.name,
                "description": kingdom.description,
                "phyla": []
            }

            for phylum in kingdom.phyla:
                phylum_data = {
                    "id": phylum.id,
                    "name": phylum.name,
                    "description": phylum.description,
                    "classes": []
                }

                for class_ in phylum.classes:
                    class_data = {
                        "id": class_.id,
                        "name": class_.name,
                        "description": class_.description,
                        "orders": []
                    }

                    for order in class_.orders:
                        order_data = {
                            "id": order.id,
                            "name": order.name,
                            "description": order.description,
                            "families": []
                        }

                        for family in order.families:
                            family_data = {
                                "id": family.id,
                                "name": family.name,
                                "description": family.description,
                                "genera": []
                            }

                            for genus in family.genera:
                                genus_data = {
                                    "id": genus.id,
                                    "name": genus.name,
                                    "description": genus.description
                                }
                                family_data["genera"].append(genus_data)

                            order_data["families"].append(family_data)

                        class_data["orders"].append(order_data)

                    phylum_data["classes"].append(class_data)

                kingdom_data["phyla"].append(phylum_data)

            domain_data["kingdoms"].append(kingdom_data)

        taxonomy_data.append(domain_data)

    return jsonify(taxonomy_data)


@app.route('/api/attempt_mutation', methods=['POST'])
def api_attempt_mutation():
    data = request.json
    seed1_id = data.get('seed1_id')
    seed2_id = data.get('seed2_id')

    # İki tohum da geçerli mi kontrol et
    seed1 = Seed.query.get(seed1_id)
    seed2 = Seed.query.get(seed2_id)

    if not seed1 or not seed2:
        return jsonify({"success": False, "message": "Geçersiz tohum seçimi"})

    # Olası mutasyonları bul
    possible_mutations = db.session.query(SeedMutation).filter(
        ((SeedMutation.parent_seed_id == seed1_id) & (SeedMutation.result_seed_id.in_(
            db.session.query(SeedMutation.result_seed_id).filter(SeedMutation.parent_seed_id == seed2_id)
        ))) |
        ((SeedMutation.parent_seed_id == seed2_id) & (SeedMutation.result_seed_id.in_(
            db.session.query(SeedMutation.result_seed_id).filter(SeedMutation.parent_seed_id == seed1_id)
        )))
    ).all()

    if not possible_mutations:
        return jsonify({"success": False, "message": "Bu tohumlar birleştirilemez"})

    # Rastgele bir mutasyon seç
    import random
    mutation = random.choice(possible_mutations)

    # Mutasyon şansını hesapla
    base_chance = (seed1.mutation_chance + seed2.mutation_chance) / 2

    # Aynı cins/familya/takım ise bonus ver
    taxonomy_bonus = 0
    if seed1.genus_id == seed2.genus_id:
        taxonomy_bonus = 0.2  # Aynı cins
    elif seed1.genus.family_id == seed2.genus.family_id:
        taxonomy_bonus = 0.1  # Aynı familya
    elif seed1.genus.family.order_id == seed2.genus.family.order_id:
        taxonomy_bonus = 0.05  # Aynı takım

    final_chance = min(0.95, base_chance + taxonomy_bonus)

    # Mutasyon başarılı mı?
    if random.random() < final_chance:
        result_seed = Seed.query.get(mutation.result_seed_id)

        # Oyuncunun açtığı tohumları güncelle
        if 'player_data' not in session:
            session['player_data'] = {}

        if 'unlocked_seeds' not in session['player_data']:
            session['player_data']['unlocked_seeds'] = []

        if result_seed.id not in session['player_data']['unlocked_seeds']:
            session['player_data']['unlocked_seeds'].append(result_seed.id)
            session.modified = True

        # Sonuç tohumunun bilgilerini döndür
        return jsonify({
            "success": True,
            "message": f"Mutasyon başarılı! {result_seed.common_name} keşfedildi!",
            "seed": {
                "id": result_seed.id,
                "scientific_name": result_seed.full_scientific_name,
                "common_name": result_seed.common_name,
                "icon": result_seed.icon,
                "tier": result_seed.tier
            }
        })
    else:
        return jsonify({"success": False, "message": "Mutasyon başarısız oldu. Tekrar deneyin!"})


# Ana oyun rotaları
@app.route('/')
def home():
    return render_template('index.html')


@app.route('/game')
def game():
    # Oyuncu verilerini başlat
    if 'player_data' not in session:
        session['player_data'] = {
            'resources': {
                'energy': 100,        # Enerji
                'water': 100,         # Saflaştırılmış su
                'nutrients': 50,      # Toprak besleyicileri/gübre
                'oxygen': 100,        # Oksijen
                'food': 50,           # Besin ürünleri
                'recycled_matter': 20, # Geri dönüştürülmüş atık
                'scientific_data': 0,  # Bilimsel veri puanları
                'robot_parts': 10      # Robot yedek parçaları
            },
            'crew': {
                'morale': 80,         # Mürettebat morali
                'effort_points': 100,  # Günlük efor puanları
                'skills': {
                    'farming': 1,     # Tarım becerisi
                    'engineering': 1, # Mühendislik becerisi
                    'science': 1      # Bilim becerisi
                }
            },
            'unlocked_seeds': [1, 2],  # Başlangıçta açık olan tohumların ID'leri
            'seed_inventory': {},      # Tohum envanteri
            'planted_crops': [],
            'level': 1,
            'day': 1,                  # Oyun günü
            'last_update': datetime.now().timestamp()
        }

    return render_template('game.html')


# Veritabanını oluştur


if __name__ == '__main__':
    with app.app_context():
        db.create_all()

        # İlk admin kullanıcısını oluştur (eğer yoksa)
        if not AdminUser.query.filter_by(username='admin').first():
            admin = AdminUser(username='admin', email='admin@example.com', is_active=True)
            admin.set_password('admin123')  # Güvenli bir şifre kullanın!
            db.session.add(admin)
            db.session.commit()

    app.run(debug=True, port=5004)