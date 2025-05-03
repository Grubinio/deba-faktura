from app import db
import hashlib
from datetime import datetime

class CategoriesTransaction(db.Model):
    __tablename__ = 'CF_categories_transactions'
    id   = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

class TransactionsRaw(db.Model):
    __tablename__ = 'CF_transactions_raw'
    id                = db.Column(db.BigInteger, primary_key=True)
    import_date       = db.Column(db.DateTime, server_default=db.func.now())
    auftraggeber      = db.Column(db.String(255))
    art               = db.Column(db.String(100))
    kontoname         = db.Column(db.String(100))
    buchungstext      = db.Column(db.Text)
    beguenstigter     = db.Column(db.String(255))
    verwendungszweck  = db.Column(db.Text)
    buchung           = db.Column(db.Date, nullable=False)
    wertstellung      = db.Column(db.Date)
    betrag            = db.Column(db.Numeric(15,2))
    waehrung          = db.Column(db.CHAR(3))
    auszugsnr         = db.Column(db.String(50))
    original_waehrung = db.Column(db.CHAR(3))

    # ───────────────────────────────────────────────────────────────────
    # Neues Feld für die ausgewählte Kategorie:
    kategorie_id      = db.Column(
        db.Integer,
        db.ForeignKey('CF_categories_transactions.id'),
        nullable=True
    )
    # Optional: direkte Beziehung
    category = db.relationship('CategoriesTransaction', backref='raw_entries')


class Transaction(db.Model):
    __tablename__ = 'CF_transactions'
    id             = db.Column(db.BigInteger, primary_key=True)
    raw_id         = db.Column(db.BigInteger,
                        db.ForeignKey('CF_transactions_raw.id', ondelete='CASCADE'),
                        nullable=False)
    auftrag_id     = db.Column(db.Integer, db.ForeignKey('auftraege.id'))
    kategorie_id   = db.Column(db.Integer,
                        db.ForeignKey('CF_categories_transactions.id'))
    betrag_orig    = db.Column(db.Numeric(15,2))
    kurs           = db.Column(db.Numeric(12,6))
    betrag_eur     = db.Column(db.Numeric(15,2))
    buchung        = db.Column(db.Date, nullable=False)
    parent_txn_id  = db.Column(db.BigInteger,
                        db.ForeignKey('CF_transactions.id'))
    splittable     = db.Column(db.Boolean, default=True, nullable=False)

    raw      = db.relationship('CF_TransactionsRaw',
                 backref=db.backref('clean_entries', cascade='all, delete-orphan'))
    children = db.relationship('Transaction',
                 backref=db.backref('parent', remote_side=[id]))

class ImportBatch(db.Model):
    __tablename__ = 'import_batches'
    id         = db.Column(db.Integer, primary_key=True)
    file_hash  = db.Column(db.String(64), unique=True, nullable=False)
    filename   = db.Column(db.String(255), nullable=False)
    imported_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

class BeneficiaryMapping(db.Model):
    __tablename__ = 'beneficiary_mappings'
    id             = db.Column(db.Integer, primary_key=True)
    beneficiary    = db.Column(db.String(255), nullable=False)
    category_id    = db.Column(
        db.Integer,
        db.ForeignKey('categories_transactions.id'),
        nullable=False
    )
    category       = db.relationship('CategoriesTransaction')
