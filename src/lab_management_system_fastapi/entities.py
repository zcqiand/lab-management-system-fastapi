from typing import Optional
import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKeyConstraint, Index, Integer, PrimaryKeyConstraint, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass


class DrizzleMigrations(Base):
    __tablename__ = '__drizzle_migrations'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='__drizzle_migrations_pkey'),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    hash: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[Optional[int]] = mapped_column(BigInteger)


class InspectionParamInterfaces(Base):
    __tablename__ = 'inspection_param_interfaces'
    __table_args__ = (
        PrimaryKeyConstraint('code', name='param_interfaces_pkey'),
    )

    code: Mapped[str] = mapped_column(Text, primary_key=True)
    component_path: Mapped[str] = mapped_column(Text, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    created_at: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''::text"))
    updated_at: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''::text"))
    name: Mapped[Optional[str]] = mapped_column(Text)
    description: Mapped[Optional[str]] = mapped_column(Text)
    is_official: Mapped[Optional[bool]] = mapped_column(Boolean)
    config: Mapped[Optional[object]] = mapped_column(JSONB)

    inspection_param_interface_links: Mapped[list['InspectionParamInterfaceLinks']] = relationship('InspectionParamInterfaceLinks', back_populates='inspection_param_interfaces')


class InspectionParameters(Base):
    __tablename__ = 'inspection_parameters'
    __table_args__ = (
        PrimaryKeyConstraint('code', name='inspection_parameters_pkey'),
    )

    code: Mapped[str] = mapped_column(Text, primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    raw_name: Mapped[str] = mapped_column(Text, nullable=False)
    canonical_name: Mapped[str] = mapped_column(Text, nullable=False)
    aliases: Mapped[object] = mapped_column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    source_type: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'official'::text"))
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    created_at: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''::text"))
    updated_at: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''::text"))
    method_text: Mapped[Optional[str]] = mapped_column(Text)
    unit: Mapped[Optional[str]] = mapped_column(Text)

    inspection_param_interface_links: Mapped[list['InspectionParamInterfaceLinks']] = relationship('InspectionParamInterfaceLinks', back_populates='inspection_parameters')
    inspection_report_name_parameters: Mapped[list['InspectionReportNameParameters']] = relationship('InspectionReportNameParameters', back_populates='inspection_parameters')
    inspection_standard_parameters: Mapped[list['InspectionStandardParameters']] = relationship('InspectionStandardParameters', back_populates='inspection_parameters')
    inspection_calculation_methods: Mapped[list['InspectionCalculationMethods']] = relationship('InspectionCalculationMethods', back_populates='inspection_parameters')
    inspection_object_parameters: Mapped[list['InspectionObjectParameters']] = relationship('InspectionObjectParameters', back_populates='inspection_parameters')
    inspection_technical_requirements: Mapped[list['InspectionTechnicalRequirements']] = relationship('InspectionTechnicalRequirements', back_populates='inspection_parameters')
    test_records: Mapped[list['TestRecords']] = relationship('TestRecords', back_populates='inspection_parameters')


class InspectionReportNames(Base):
    __tablename__ = 'inspection_report_names'
    __table_args__ = (
        PrimaryKeyConstraint('code', name='inspection_report_names_pkey'),
    )

    code: Mapped[str] = mapped_column(Text, primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    created_at: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''::text"))
    updated_at: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''::text"))
    full_name: Mapped[Optional[str]] = mapped_column(Text)
    template_path: Mapped[Optional[str]] = mapped_column(Text)
    summary_name: Mapped[Optional[str]] = mapped_column(Text)
    ext_fields: Mapped[Optional[object]] = mapped_column(JSONB)
    description: Mapped[Optional[str]] = mapped_column(Text)

    inspection_param_interface_links: Mapped[list['InspectionParamInterfaceLinks']] = relationship('InspectionParamInterfaceLinks', back_populates='inspection_report_names')
    inspection_report_name_parameters: Mapped[list['InspectionReportNameParameters']] = relationship('InspectionReportNameParameters', back_populates='inspection_report_names')
    inspection_report_name_standards: Mapped[list['InspectionReportNameStandards']] = relationship('InspectionReportNameStandards', back_populates='inspection_report_names')
    inspection_calculation_methods: Mapped[list['InspectionCalculationMethods']] = relationship('InspectionCalculationMethods', back_populates='inspection_report_names')
    inspection_object_report_names: Mapped[list['InspectionObjectReportNames']] = relationship('InspectionObjectReportNames', back_populates='inspection_report_names')
    sample_receipts: Mapped[list['SampleReceipts']] = relationship('SampleReceipts', back_populates='inspection_report_names')


class InspectionSpecialties(Base):
    __tablename__ = 'inspection_specialties'
    __table_args__ = (
        PrimaryKeyConstraint('code', name='inspection_specialties_pkey'),
    )

    code: Mapped[str] = mapped_column(Text, primary_key=True)
    official_no: Mapped[str] = mapped_column(Text, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    is_official: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('true'))
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('true'))
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    created_at: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''::text"))
    updated_at: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''::text"))

    contracts: Mapped[list['Contracts']] = relationship('Contracts', back_populates='inspection_specialties')
    inspection_objects: Mapped[list['InspectionObjects']] = relationship('InspectionObjects', back_populates='inspection_specialties')
    inspection_specialty_objects: Mapped[list['InspectionSpecialtyObjects']] = relationship('InspectionSpecialtyObjects', back_populates='inspection_specialties')


class InspectionStandards(Base):
    __tablename__ = 'inspection_standards'
    __table_args__ = (
        PrimaryKeyConstraint('code', name='inspection_standards_pkey'),
    )

    code: Mapped[str] = mapped_column(Text, primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'active'::text"))
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    created_at: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''::text"))
    updated_at: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''::text"))
    version: Mapped[Optional[str]] = mapped_column(Text)
    source_document_id: Mapped[Optional[str]] = mapped_column(Text)
    source_hash: Mapped[Optional[str]] = mapped_column(Text)

    inspection_report_name_standards: Mapped[list['InspectionReportNameStandards']] = relationship('InspectionReportNameStandards', back_populates='inspection_standards')
    inspection_standard_parameters: Mapped[list['InspectionStandardParameters']] = relationship('InspectionStandardParameters', back_populates='inspection_standards')
    inspection_calculation_methods: Mapped[list['InspectionCalculationMethods']] = relationship('InspectionCalculationMethods', back_populates='inspection_standards')
    inspection_object_standards: Mapped[list['InspectionObjectStandards']] = relationship('InspectionObjectStandards', back_populates='inspection_standards')
    inspection_technical_requirements: Mapped[list['InspectionTechnicalRequirements']] = relationship('InspectionTechnicalRequirements', back_populates='inspection_standards')
    test_records: Mapped[list['TestRecords']] = relationship('TestRecords', back_populates='inspection_standards')


class Contracts(Base):
    __tablename__ = 'contracts'
    __table_args__ = (
        ForeignKeyConstraint(['inspection_specialty_code'], ['inspection_specialties.code'], ondelete='SET NULL', name='contracts_specialty_fk'),
        PrimaryKeyConstraint('id', name='contracts_pkey'),
        Index('idx_contracts_tenant', 'tenant_id'),
        Index('idx_contracts_tenant_code', 'tenant_id', 'contract_code', unique=True)
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    contract_code: Mapped[str] = mapped_column(Text, nullable=False)
    client_unit: Mapped[str] = mapped_column(Text, nullable=False)
    project_name: Mapped[str] = mapped_column(Text, nullable=False)
    construction_unit: Mapped[str] = mapped_column(Text, nullable=False)
    witness_unit: Mapped[str] = mapped_column(Text, nullable=False)
    witness: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'active'::text"))
    created_at: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''::text"))
    updated_at: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''::text"))
    tenant_id: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''::text"))
    project_location: Mapped[Optional[str]] = mapped_column(Text)
    inspection_specialty_code: Mapped[Optional[str]] = mapped_column(Text)
    building_unit: Mapped[Optional[str]] = mapped_column(Text)
    supervisor_unit: Mapped[Optional[str]] = mapped_column(Text)
    inspection_person: Mapped[Optional[str]] = mapped_column(Text)
    inspection_phone: Mapped[Optional[str]] = mapped_column(Text)
    witness_phone: Mapped[Optional[str]] = mapped_column(Text)
    contact_person: Mapped[Optional[str]] = mapped_column(Text)
    contact_phone: Mapped[Optional[str]] = mapped_column(Text)
    entrusted_date: Mapped[Optional[str]] = mapped_column(Text)

    inspection_specialties: Mapped[Optional['InspectionSpecialties']] = relationship('InspectionSpecialties', back_populates='contracts')
    sample_receipts: Mapped[list['SampleReceipts']] = relationship('SampleReceipts', back_populates='contract')


class InspectionObjects(Base):
    __tablename__ = 'inspection_objects'
    __table_args__ = (
        ForeignKeyConstraint(['inspection_specialty_code'], ['inspection_specialties.code'], ondelete='RESTRICT', name='objects_specialty_fk'),
        PrimaryKeyConstraint('code', name='inspection_objects_pkey'),
        Index('idx_objects_specialty', 'inspection_specialty_code')
    )

    code: Mapped[str] = mapped_column(Text, primary_key=True)
    inspection_specialty_code: Mapped[str] = mapped_column(Text, nullable=False)
    source_project_no: Mapped[str] = mapped_column(Text, nullable=False)
    source_project_name: Mapped[str] = mapped_column(Text, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    is_optional_for_qualification: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('false'))
    is_official: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('true'))
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('true'))
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    created_at: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''::text"))
    updated_at: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''::text"))

    inspection_specialties: Mapped['InspectionSpecialties'] = relationship('InspectionSpecialties', back_populates='inspection_objects')
    inspection_brands: Mapped[list['InspectionBrands']] = relationship('InspectionBrands', back_populates='inspection_objects')
    inspection_calculation_methods: Mapped[list['InspectionCalculationMethods']] = relationship('InspectionCalculationMethods', back_populates='inspection_objects')
    inspection_grades: Mapped[list['InspectionGrades']] = relationship('InspectionGrades', back_populates='inspection_objects')
    inspection_models: Mapped[list['InspectionModels']] = relationship('InspectionModels', back_populates='inspection_objects')
    inspection_object_parameters: Mapped[list['InspectionObjectParameters']] = relationship('InspectionObjectParameters', back_populates='inspection_objects')
    inspection_object_report_names: Mapped[list['InspectionObjectReportNames']] = relationship('InspectionObjectReportNames', back_populates='inspection_objects')
    inspection_object_standards: Mapped[list['InspectionObjectStandards']] = relationship('InspectionObjectStandards', back_populates='inspection_objects')
    inspection_specialty_objects: Mapped[list['InspectionSpecialtyObjects']] = relationship('InspectionSpecialtyObjects', back_populates='inspection_objects')
    inspection_specs: Mapped[list['InspectionSpecs']] = relationship('InspectionSpecs', back_populates='inspection_objects')
    inspection_technical_requirements: Mapped[list['InspectionTechnicalRequirements']] = relationship('InspectionTechnicalRequirements', back_populates='inspection_objects')


class InspectionParamInterfaceLinks(Base):
    __tablename__ = 'inspection_param_interface_links'
    __table_args__ = (
        ForeignKeyConstraint(['inspection_parameter_code'], ['inspection_parameters.code'], ondelete='CASCADE', name='pil_param_fk'),
        ForeignKeyConstraint(['param_interface_code'], ['inspection_param_interfaces.code'], ondelete='CASCADE', name='pil_interface_fk'),
        ForeignKeyConstraint(['report_name_code'], ['inspection_report_names.code'], ondelete='SET NULL', name='pil_report_fk'),
        PrimaryKeyConstraint('inspection_parameter_code', 'param_interface_code', name='param_interface_links_pkey'),
        Index('idx_pil_param', 'inspection_parameter_code')
    )

    inspection_parameter_code: Mapped[str] = mapped_column(Text, primary_key=True)
    param_interface_code: Mapped[str] = mapped_column(Text, primary_key=True)
    created_at: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''::text"))
    updated_at: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''::text"))
    report_name_code: Mapped[Optional[str]] = mapped_column(Text)
    config: Mapped[Optional[object]] = mapped_column(JSONB)

    inspection_parameters: Mapped['InspectionParameters'] = relationship('InspectionParameters', back_populates='inspection_param_interface_links')
    inspection_param_interfaces: Mapped['InspectionParamInterfaces'] = relationship('InspectionParamInterfaces', back_populates='inspection_param_interface_links')
    inspection_report_names: Mapped[Optional['InspectionReportNames']] = relationship('InspectionReportNames', back_populates='inspection_param_interface_links')


class InspectionReportNameParameters(Base):
    __tablename__ = 'inspection_report_name_parameters'
    __table_args__ = (
        ForeignKeyConstraint(['inspection_parameter_code'], ['inspection_parameters.code'], ondelete='CASCADE', name='rn_param_parameter_fk'),
        ForeignKeyConstraint(['report_name_code'], ['inspection_report_names.code'], ondelete='CASCADE', name='rn_param_report_fk'),
        PrimaryKeyConstraint('report_name_code', 'inspection_parameter_code', name='inspection_report_name_parameters_pkey'),
        Index('idx_rn_param_report', 'report_name_code')
    )

    report_name_code: Mapped[str] = mapped_column(Text, primary_key=True)
    inspection_parameter_code: Mapped[str] = mapped_column(Text, primary_key=True)
    created_at: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''::text"))
    updated_at: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''::text"))
    remark: Mapped[Optional[str]] = mapped_column(Text)

    inspection_parameters: Mapped['InspectionParameters'] = relationship('InspectionParameters', back_populates='inspection_report_name_parameters')
    inspection_report_names: Mapped['InspectionReportNames'] = relationship('InspectionReportNames', back_populates='inspection_report_name_parameters')


class InspectionReportNameStandards(Base):
    __tablename__ = 'inspection_report_name_standards'
    __table_args__ = (
        ForeignKeyConstraint(['inspection_standard_code'], ['inspection_standards.code'], ondelete='CASCADE', name='rn_std_standard_fk'),
        ForeignKeyConstraint(['report_name_code'], ['inspection_report_names.code'], ondelete='CASCADE', name='rn_std_report_fk'),
        PrimaryKeyConstraint('report_name_code', 'inspection_standard_code', 'role', name='inspection_report_name_standards_pkey'),
        Index('idx_rn_std_report', 'report_name_code')
    )

    report_name_code: Mapped[str] = mapped_column(Text, primary_key=True)
    inspection_standard_code: Mapped[str] = mapped_column(Text, primary_key=True)
    role: Mapped[str] = mapped_column(Text, primary_key=True)
    created_at: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''::text"))
    updated_at: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''::text"))
    remark: Mapped[Optional[str]] = mapped_column(Text)

    inspection_standards: Mapped['InspectionStandards'] = relationship('InspectionStandards', back_populates='inspection_report_name_standards')
    inspection_report_names: Mapped['InspectionReportNames'] = relationship('InspectionReportNames', back_populates='inspection_report_name_standards')


class InspectionStandardParameters(Base):
    __tablename__ = 'inspection_standard_parameters'
    __table_args__ = (
        ForeignKeyConstraint(['inspection_parameter_code'], ['inspection_parameters.code'], ondelete='CASCADE', name='std_param_parameter_fk'),
        ForeignKeyConstraint(['inspection_standard_code'], ['inspection_standards.code'], ondelete='CASCADE', name='std_param_standard_fk'),
        PrimaryKeyConstraint('inspection_standard_code', 'inspection_parameter_code', name='inspection_standard_parameters_pkey'),
        Index('idx_std_param_standard', 'inspection_standard_code')
    )

    inspection_standard_code: Mapped[str] = mapped_column(Text, primary_key=True)
    inspection_parameter_code: Mapped[str] = mapped_column(Text, primary_key=True)
    created_at: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''::text"))
    updated_at: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''::text"))

    inspection_parameters: Mapped['InspectionParameters'] = relationship('InspectionParameters', back_populates='inspection_standard_parameters')
    inspection_standards: Mapped['InspectionStandards'] = relationship('InspectionStandards', back_populates='inspection_standard_parameters')


class InspectionBrands(Base):
    __tablename__ = 'inspection_brands'
    __table_args__ = (
        ForeignKeyConstraint(['inspection_object_code'], ['inspection_objects.code'], ondelete='SET NULL', name='brands_object_fk'),
        PrimaryKeyConstraint('code', name='inspection_brands_pkey'),
        Index('idx_brands_tenant', 'tenant_id'),
        Index('idx_brands_tenant_code', 'tenant_id', 'code', unique=True),
        Index('idx_inspection_brands_object', 'inspection_object_code')
    )

    code: Mapped[str] = mapped_column(Text, primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    created_at: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''::text"))
    updated_at: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''::text"))
    tenant_id: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''::text"))
    inspection_object_code: Mapped[Optional[str]] = mapped_column(Text)
    remark: Mapped[Optional[str]] = mapped_column(Text)

    inspection_objects: Mapped[Optional['InspectionObjects']] = relationship('InspectionObjects', back_populates='inspection_brands')
    inspection_technical_requirements: Mapped[list['InspectionTechnicalRequirements']] = relationship('InspectionTechnicalRequirements', back_populates='inspection_brands')


class InspectionCalculationMethods(Base):
    __tablename__ = 'inspection_calculation_methods'
    __table_args__ = (
        ForeignKeyConstraint(['inspection_object_code'], ['inspection_objects.code'], ondelete='CASCADE', name='calc_rule_object_fk'),
        ForeignKeyConstraint(['inspection_parameter_code'], ['inspection_parameters.code'], ondelete='CASCADE', name='calc_rule_parameter_fk'),
        ForeignKeyConstraint(['report_name_code'], ['inspection_report_names.code'], ondelete='SET NULL', name='calc_rule_report_fk'),
        ForeignKeyConstraint(['testing_standard_code'], ['inspection_standards.code'], ondelete='SET NULL', name='calc_rule_standard_fk'),
        PrimaryKeyConstraint('inspection_object_code', 'inspection_parameter_code', name='inspection_calculation_rules_pkey'),
        Index('idx_calc_method_object', 'inspection_object_code')
    )

    inspection_object_code: Mapped[str] = mapped_column(Text, primary_key=True)
    inspection_parameter_code: Mapped[str] = mapped_column(Text, primary_key=True)
    algorithm_type: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'manual'::text"))
    specimen_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('1'))
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    created_at: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''::text"))
    updated_at: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''::text"))
    testing_standard_code: Mapped[Optional[str]] = mapped_column(Text)
    report_name_code: Mapped[Optional[str]] = mapped_column(Text)
    formula: Mapped[Optional[str]] = mapped_column(Text)
    conditions: Mapped[Optional[str]] = mapped_column(Text)
    rounding_rule: Mapped[Optional[str]] = mapped_column(Text)
    remark: Mapped[Optional[str]] = mapped_column(Text)

    inspection_objects: Mapped['InspectionObjects'] = relationship('InspectionObjects', back_populates='inspection_calculation_methods')
    inspection_parameters: Mapped['InspectionParameters'] = relationship('InspectionParameters', back_populates='inspection_calculation_methods')
    inspection_report_names: Mapped[Optional['InspectionReportNames']] = relationship('InspectionReportNames', back_populates='inspection_calculation_methods')
    inspection_standards: Mapped[Optional['InspectionStandards']] = relationship('InspectionStandards', back_populates='inspection_calculation_methods')


class InspectionGrades(Base):
    __tablename__ = 'inspection_grades'
    __table_args__ = (
        ForeignKeyConstraint(['inspection_object_code'], ['inspection_objects.code'], ondelete='SET NULL', name='grades_object_fk'),
        PrimaryKeyConstraint('code', name='inspection_grades_pkey'),
        Index('idx_grades_tenant', 'tenant_id'),
        Index('idx_grades_tenant_code', 'tenant_id', 'code', unique=True),
        Index('idx_inspection_grades_object', 'inspection_object_code')
    )

    code: Mapped[str] = mapped_column(Text, primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    created_at: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''::text"))
    updated_at: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''::text"))
    tenant_id: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''::text"))
    inspection_object_code: Mapped[Optional[str]] = mapped_column(Text)
    remark: Mapped[Optional[str]] = mapped_column(Text)

    inspection_objects: Mapped[Optional['InspectionObjects']] = relationship('InspectionObjects', back_populates='inspection_grades')
    inspection_technical_requirements: Mapped[list['InspectionTechnicalRequirements']] = relationship('InspectionTechnicalRequirements', back_populates='inspection_grades')


class InspectionModels(Base):
    __tablename__ = 'inspection_models'
    __table_args__ = (
        ForeignKeyConstraint(['inspection_object_code'], ['inspection_objects.code'], ondelete='SET NULL', name='models_object_fk'),
        PrimaryKeyConstraint('code', name='inspection_models_pkey'),
        Index('idx_inspection_models_object', 'inspection_object_code'),
        Index('idx_models_tenant', 'tenant_id'),
        Index('idx_models_tenant_code', 'tenant_id', 'code', unique=True)
    )

    code: Mapped[str] = mapped_column(Text, primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    created_at: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''::text"))
    updated_at: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''::text"))
    tenant_id: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''::text"))
    inspection_object_code: Mapped[Optional[str]] = mapped_column(Text)
    remark: Mapped[Optional[str]] = mapped_column(Text)

    inspection_objects: Mapped[Optional['InspectionObjects']] = relationship('InspectionObjects', back_populates='inspection_models')
    inspection_technical_requirements: Mapped[list['InspectionTechnicalRequirements']] = relationship('InspectionTechnicalRequirements', back_populates='inspection_models')


class InspectionObjectParameters(Base):
    __tablename__ = 'inspection_object_parameters'
    __table_args__ = (
        ForeignKeyConstraint(['inspection_object_code'], ['inspection_objects.code'], ondelete='CASCADE', name='obj_params_object_fk'),
        ForeignKeyConstraint(['inspection_parameter_code'], ['inspection_parameters.code'], ondelete='CASCADE', name='obj_params_parameter_fk'),
        PrimaryKeyConstraint('inspection_object_code', 'inspection_parameter_code', name='inspection_object_parameters_pkey'),
        Index('idx_obj_params_object', 'inspection_object_code'),
        Index('idx_obj_params_param', 'inspection_parameter_code')
    )

    inspection_object_code: Mapped[str] = mapped_column(Text, primary_key=True)
    inspection_parameter_code: Mapped[str] = mapped_column(Text, primary_key=True)
    qualification_level: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'QUALIFIED'::text"))
    created_at: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''::text"))
    updated_at: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''::text"))
    source_page: Mapped[Optional[int]] = mapped_column(Integer)
    remark: Mapped[Optional[str]] = mapped_column(Text)

    inspection_objects: Mapped['InspectionObjects'] = relationship('InspectionObjects', back_populates='inspection_object_parameters')
    inspection_parameters: Mapped['InspectionParameters'] = relationship('InspectionParameters', back_populates='inspection_object_parameters')


class InspectionObjectReportNames(Base):
    __tablename__ = 'inspection_object_report_names'
    __table_args__ = (
        ForeignKeyConstraint(['inspection_object_code'], ['inspection_objects.code'], ondelete='CASCADE', name='obj_rn_object_fk'),
        ForeignKeyConstraint(['report_name_code'], ['inspection_report_names.code'], ondelete='CASCADE', name='obj_rn_report_fk'),
        PrimaryKeyConstraint('inspection_object_code', 'report_name_code', name='inspection_object_report_names_pkey'),
        Index('idx_obj_rn_object', 'inspection_object_code')
    )

    inspection_object_code: Mapped[str] = mapped_column(Text, primary_key=True)
    report_name_code: Mapped[str] = mapped_column(Text, primary_key=True)
    created_at: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''::text"))
    updated_at: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''::text"))
    remark: Mapped[Optional[str]] = mapped_column(Text)

    inspection_objects: Mapped['InspectionObjects'] = relationship('InspectionObjects', back_populates='inspection_object_report_names')
    inspection_report_names: Mapped['InspectionReportNames'] = relationship('InspectionReportNames', back_populates='inspection_object_report_names')


class InspectionObjectStandards(Base):
    __tablename__ = 'inspection_object_standards'
    __table_args__ = (
        ForeignKeyConstraint(['inspection_object_code'], ['inspection_objects.code'], ondelete='CASCADE', name='obj_std_object_fk'),
        ForeignKeyConstraint(['inspection_standard_code'], ['inspection_standards.code'], ondelete='CASCADE', name='obj_std_standard_fk'),
        PrimaryKeyConstraint('inspection_object_code', 'inspection_standard_code', 'role', name='inspection_object_standards_pkey'),
        Index('idx_obj_std_object', 'inspection_object_code')
    )

    inspection_object_code: Mapped[str] = mapped_column(Text, primary_key=True)
    inspection_standard_code: Mapped[str] = mapped_column(Text, primary_key=True)
    role: Mapped[str] = mapped_column(Text, primary_key=True)
    created_at: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''::text"))
    updated_at: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''::text"))
    remark: Mapped[Optional[str]] = mapped_column(Text)

    inspection_objects: Mapped['InspectionObjects'] = relationship('InspectionObjects', back_populates='inspection_object_standards')
    inspection_standards: Mapped['InspectionStandards'] = relationship('InspectionStandards', back_populates='inspection_object_standards')


class InspectionSpecialtyObjects(Base):
    __tablename__ = 'inspection_specialty_objects'
    __table_args__ = (
        ForeignKeyConstraint(['inspection_object_code'], ['inspection_objects.code'], ondelete='CASCADE', name='specialty_objects_object_fk'),
        ForeignKeyConstraint(['inspection_specialty_code'], ['inspection_specialties.code'], ondelete='CASCADE', name='specialty_objects_specialty_fk'),
        PrimaryKeyConstraint('inspection_specialty_code', 'inspection_object_code', name='inspection_specialty_objects_pkey')
    )

    inspection_specialty_code: Mapped[str] = mapped_column(Text, primary_key=True)
    inspection_object_code: Mapped[str] = mapped_column(Text, primary_key=True)
    created_at: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''::text"))
    updated_at: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''::text"))
    remark: Mapped[Optional[str]] = mapped_column(Text)

    inspection_objects: Mapped['InspectionObjects'] = relationship('InspectionObjects', back_populates='inspection_specialty_objects')
    inspection_specialties: Mapped['InspectionSpecialties'] = relationship('InspectionSpecialties', back_populates='inspection_specialty_objects')


class InspectionSpecs(Base):
    __tablename__ = 'inspection_specs'
    __table_args__ = (
        ForeignKeyConstraint(['inspection_object_code'], ['inspection_objects.code'], ondelete='SET NULL', name='specs_object_fk'),
        PrimaryKeyConstraint('code', name='inspection_specs_pkey'),
        Index('idx_inspection_specs_object', 'inspection_object_code'),
        Index('idx_specs_tenant', 'tenant_id'),
        Index('idx_specs_tenant_code', 'tenant_id', 'code', unique=True)
    )

    code: Mapped[str] = mapped_column(Text, primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    created_at: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''::text"))
    updated_at: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''::text"))
    tenant_id: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''::text"))
    inspection_object_code: Mapped[Optional[str]] = mapped_column(Text)
    remark: Mapped[Optional[str]] = mapped_column(Text)

    inspection_objects: Mapped[Optional['InspectionObjects']] = relationship('InspectionObjects', back_populates='inspection_specs')
    inspection_technical_requirements: Mapped[list['InspectionTechnicalRequirements']] = relationship('InspectionTechnicalRequirements', back_populates='inspection_specs')


class SampleReceipts(Base):
    __tablename__ = 'sample_receipts'
    __table_args__ = (
        ForeignKeyConstraint(['category_code'], ['inspection_report_names.code'], ondelete='RESTRICT', name='receipts_category_fk'),
        ForeignKeyConstraint(['contract_id'], ['contracts.id'], ondelete='RESTRICT', name='sample_receipts_contract_fk'),
        PrimaryKeyConstraint('id', name='sample_receipts_pkey'),
        Index('idx_receipts_tenant', 'tenant_id'),
        Index('idx_receipts_tenant_commission', 'tenant_id', 'commission_code', unique=True),
        Index('idx_sample_receipts_category', 'category_code'),
        Index('idx_sample_receipts_contract', 'contract_id'),
        Index('idx_sample_receipts_flow_status', 'flow_status')
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    contract_id: Mapped[str] = mapped_column(Text, nullable=False)
    commission_code: Mapped[str] = mapped_column(Text, nullable=False)
    commission_date: Mapped[str] = mapped_column(Text, nullable=False)
    category_code: Mapped[str] = mapped_column(Text, nullable=False)
    received_by: Mapped[str] = mapped_column(Text, nullable=False)
    sample_source: Mapped[str] = mapped_column(Text, nullable=False)
    test_category: Mapped[str] = mapped_column(Text, nullable=False)
    flow_status: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'receiving'::text"))
    flow_history: Mapped[object] = mapped_column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    created_at: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''::text"))
    updated_at: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''::text"))
    tenant_id: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''::text"))
    commission_register_code: Mapped[Optional[str]] = mapped_column(Text)
    commission_register_date: Mapped[Optional[str]] = mapped_column(Text)
    project_name: Mapped[Optional[str]] = mapped_column(Text)
    client_unit: Mapped[Optional[str]] = mapped_column(Text)
    building_unit: Mapped[Optional[str]] = mapped_column(Text)
    supervisor_unit: Mapped[Optional[str]] = mapped_column(Text)
    construction_unit: Mapped[Optional[str]] = mapped_column(Text)
    witness_unit: Mapped[Optional[str]] = mapped_column(Text)
    sampling_location: Mapped[Optional[str]] = mapped_column(Text)
    witness: Mapped[Optional[str]] = mapped_column(Text)
    witness_phone: Mapped[Optional[str]] = mapped_column(Text)
    inspector: Mapped[Optional[str]] = mapped_column(Text)
    inspector_phone: Mapped[Optional[str]] = mapped_column(Text)
    test_environment: Mapped[Optional[str]] = mapped_column(Text)
    main_equipment: Mapped[Optional[str]] = mapped_column(Text)
    test_operator: Mapped[Optional[str]] = mapped_column(Text)
    test_start_date: Mapped[Optional[str]] = mapped_column(Text)
    test_end_date: Mapped[Optional[str]] = mapped_column(Text)
    original_record_no: Mapped[Optional[str]] = mapped_column(Text)
    remark: Mapped[Optional[str]] = mapped_column(Text)
    judgment_basis: Mapped[Optional[object]] = mapped_column(JSONB)
    testing_basis: Mapped[Optional[object]] = mapped_column(JSONB)
    test_parameters: Mapped[Optional[object]] = mapped_column(JSONB)
    last_submitted_by: Mapped[Optional[str]] = mapped_column(Text)
    assignee_id: Mapped[Optional[str]] = mapped_column(Text)
    assignee_name: Mapped[Optional[str]] = mapped_column(Text)
    planned_test_date: Mapped[Optional[str]] = mapped_column(Text)
    report_code: Mapped[Optional[str]] = mapped_column(Text)
    report_date: Mapped[Optional[str]] = mapped_column(Text)
    conclusion: Mapped[Optional[str]] = mapped_column(Text)
    result: Mapped[Optional[str]] = mapped_column(Text)
    issued_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True))

    inspection_report_names: Mapped['InspectionReportNames'] = relationship('InspectionReportNames', back_populates='sample_receipts')
    contract: Mapped['Contracts'] = relationship('Contracts', back_populates='sample_receipts')
    samples: Mapped[list['Samples']] = relationship('Samples', back_populates='receipt')


class InspectionTechnicalRequirements(Base):
    __tablename__ = 'inspection_technical_requirements'
    __table_args__ = (
        ForeignKeyConstraint(['brand'], ['inspection_brands.code'], ondelete='SET NULL', name='tech_req_brand_fk'),
        ForeignKeyConstraint(['grade'], ['inspection_grades.code'], ondelete='SET NULL', name='tech_req_grade_fk'),
        ForeignKeyConstraint(['inspection_object_code'], ['inspection_objects.code'], ondelete='CASCADE', name='tech_req_object_fk'),
        ForeignKeyConstraint(['inspection_parameter_code'], ['inspection_parameters.code'], ondelete='CASCADE', name='tech_req_parameter_fk'),
        ForeignKeyConstraint(['judgment_standard_code'], ['inspection_standards.code'], ondelete='RESTRICT', name='tech_req_judgment_standard_fk'),
        ForeignKeyConstraint(['model'], ['inspection_models.code'], ondelete='SET NULL', name='tech_req_model_fk'),
        ForeignKeyConstraint(['spec'], ['inspection_specs.code'], ondelete='SET NULL', name='tech_req_spec_fk'),
        PrimaryKeyConstraint('inspection_object_code', 'inspection_parameter_code', 'judgment_standard_code', name='inspection_technical_requirements_pkey'),
        Index('idx_tech_req_object', 'inspection_object_code'),
        Index('idx_tech_req_parameter', 'inspection_parameter_code'),
        Index('idx_tech_req_tenant', 'tenant_id')
    )

    inspection_object_code: Mapped[str] = mapped_column(Text, primary_key=True)
    inspection_parameter_code: Mapped[str] = mapped_column(Text, primary_key=True)
    judgment_standard_code: Mapped[str] = mapped_column(Text, primary_key=True)
    value_type: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'numeric'::text"))
    comparison: Mapped[str] = mapped_column(Text, nullable=False)
    judgment_mode: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'manual'::text"))
    verification_status: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'draft'::text"))
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    created_at: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''::text"))
    updated_at: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''::text"))
    tenant_id: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''::text"))
    conditions: Mapped[Optional[str]] = mapped_column(Text)
    min_value: Mapped[Optional[int]] = mapped_column(Integer)
    max_value: Mapped[Optional[int]] = mapped_column(Integer)
    target_value: Mapped[Optional[str]] = mapped_column(Text)
    expression: Mapped[Optional[str]] = mapped_column(Text)
    unit: Mapped[Optional[str]] = mapped_column(Text)
    clause: Mapped[Optional[str]] = mapped_column(Text)
    source_page: Mapped[Optional[int]] = mapped_column(Integer)
    source_hash: Mapped[Optional[str]] = mapped_column(Text)
    brand: Mapped[Optional[str]] = mapped_column(Text)
    model: Mapped[Optional[str]] = mapped_column(Text)
    grade: Mapped[Optional[str]] = mapped_column(Text)
    spec: Mapped[Optional[str]] = mapped_column(Text)
    sieve: Mapped[Optional[str]] = mapped_column(Text)
    remark: Mapped[Optional[str]] = mapped_column(Text)

    inspection_brands: Mapped[Optional['InspectionBrands']] = relationship('InspectionBrands', back_populates='inspection_technical_requirements')
    inspection_grades: Mapped[Optional['InspectionGrades']] = relationship('InspectionGrades', back_populates='inspection_technical_requirements')
    inspection_objects: Mapped['InspectionObjects'] = relationship('InspectionObjects', back_populates='inspection_technical_requirements')
    inspection_parameters: Mapped['InspectionParameters'] = relationship('InspectionParameters', back_populates='inspection_technical_requirements')
    inspection_standards: Mapped['InspectionStandards'] = relationship('InspectionStandards', back_populates='inspection_technical_requirements')
    inspection_models: Mapped[Optional['InspectionModels']] = relationship('InspectionModels', back_populates='inspection_technical_requirements')
    inspection_specs: Mapped[Optional['InspectionSpecs']] = relationship('InspectionSpecs', back_populates='inspection_technical_requirements')


class Samples(Base):
    __tablename__ = 'samples'
    __table_args__ = (
        ForeignKeyConstraint(['receipt_id'], ['sample_receipts.id'], ondelete='CASCADE', name='samples_receipt_fk'),
        PrimaryKeyConstraint('id', name='samples_pkey'),
        Index('idx_samples_receipt', 'receipt_id'),
        Index('idx_samples_tenant', 'tenant_id')
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    receipt_id: Mapped[str] = mapped_column(Text, nullable=False)
    sample_code: Mapped[str] = mapped_column(Text, nullable=False)
    ext: Mapped[object] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    created_at: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''::text"))
    updated_at: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''::text"))
    tenant_id: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''::text"))
    sample_name: Mapped[Optional[str]] = mapped_column(Text)
    model: Mapped[Optional[str]] = mapped_column(Text)
    specification: Mapped[Optional[str]] = mapped_column(Text)
    grade: Mapped[Optional[str]] = mapped_column(Text)
    brand: Mapped[Optional[str]] = mapped_column(Text)
    manufacturer: Mapped[Optional[str]] = mapped_column(Text)
    structural_part: Mapped[Optional[str]] = mapped_column(Text)
    represent_quantity: Mapped[Optional[str]] = mapped_column(Text)
    sample_quantity: Mapped[Optional[str]] = mapped_column(Text)
    batch_number: Mapped[Optional[str]] = mapped_column(Text)
    supply_unit: Mapped[Optional[str]] = mapped_column(Text)
    arrival_date: Mapped[Optional[str]] = mapped_column(Text)
    sampling_date: Mapped[Optional[str]] = mapped_column(Text)
    curing_condition: Mapped[Optional[str]] = mapped_column(Text)
    age: Mapped[Optional[str]] = mapped_column(Text)
    remark: Mapped[Optional[str]] = mapped_column(Text)

    receipt: Mapped['SampleReceipts'] = relationship('SampleReceipts', back_populates='samples')
    test_records: Mapped[list['TestRecords']] = relationship('TestRecords', back_populates='sample')


class TestRecords(Base):
    __tablename__ = 'test_records'
    __table_args__ = (
        ForeignKeyConstraint(['parameter_code'], ['inspection_parameters.code'], ondelete='RESTRICT', name='testrec_param_fk'),
        ForeignKeyConstraint(['sample_id'], ['samples.id'], ondelete='CASCADE', name='test_records_sample_fk'),
        ForeignKeyConstraint(['standard_code'], ['inspection_standards.code'], ondelete='SET NULL', name='testrec_standard_fk'),
        PrimaryKeyConstraint('id', name='test_records_pkey'),
        Index('idx_test_records_sample', 'sample_id'),
        Index('idx_test_records_tenant', 'tenant_id')
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    sample_id: Mapped[str] = mapped_column(Text, nullable=False)
    parameter_code: Mapped[str] = mapped_column(Text, nullable=False)
    requirement: Mapped[str] = mapped_column(Text, nullable=False)
    result: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''::text"))
    updated_at: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''::text"))
    tenant_id: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''::text"))
    standard_code: Mapped[Optional[str]] = mapped_column(Text)
    requirement_code: Mapped[Optional[str]] = mapped_column(Text)
    verdict: Mapped[Optional[str]] = mapped_column(Text)

    inspection_parameters: Mapped['InspectionParameters'] = relationship('InspectionParameters', back_populates='test_records')
    sample: Mapped['Samples'] = relationship('Samples', back_populates='test_records')
    inspection_standards: Mapped[Optional['InspectionStandards']] = relationship('InspectionStandards', back_populates='test_records')
