-- CreateEnum
CREATE TYPE "Role" AS ENUM ('SUPER_ADMIN', 'CB_ADMIN', 'LEAD_AUDITOR', 'TECHNICAL_REVIEWER', 'DECISION_MAKER', 'CLIENT_ADMIN');

-- CreateEnum
CREATE TYPE "CertificateStatus" AS ENUM ('DRAFT', 'ACTIVE', 'SUSPENDED', 'WITHDRAWN', 'EXPIRED');

-- CreateEnum
CREATE TYPE "CertHistoryAction" AS ENUM ('ISSUED', 'RENEWED', 'SURVEILLANCE_PASSED', 'SUSPENDED', 'SUSPENSION_LIFTED', 'WITHDRAWN', 'EXPIRED', 'SCOPE_EXTENDED', 'SCOPE_REDUCED', 'TRANSFER_IN', 'TRANSFER_OUT');

-- CreateEnum
CREATE TYPE "AuditProgramStatus" AS ENUM ('DRAFT', 'ACTIVE', 'COMPLETED', 'CANCELLED');

-- CreateEnum
CREATE TYPE "AuditType" AS ENUM ('STAGE1', 'STAGE2', 'SURVEILLANCE', 'RECERTIFICATION', 'TRANSFER', 'SPECIAL', 'INTERNAL');

-- CreateEnum
CREATE TYPE "AuditStatus" AS ENUM ('DRAFT', 'SCHEDULED', 'IN_PROGRESS', 'REPORT_DRAFT', 'CLIENT_REVIEW', 'SUBMITTED', 'TECHNICAL_REVIEW', 'DECISION_PENDING', 'DECIDED', 'CLOSED', 'CANCELLED');

-- CreateEnum
CREATE TYPE "TeamMemberRole" AS ENUM ('LEAD_AUDITOR', 'AUDITOR', 'TECHNICAL_EXPERT', 'TRAINEE', 'OBSERVER');

-- CreateEnum
CREATE TYPE "FindingType" AS ENUM ('NC_MAJOR', 'NC_MINOR', 'OBSERVATION', 'OFI');

-- CreateEnum
CREATE TYPE "NCVerificationStatus" AS ENUM ('OPEN', 'CLIENT_RESPONDED', 'ACCEPTED', 'CLOSED');

-- CreateEnum
CREATE TYPE "ComplaintType" AS ENUM ('AUDIT_CONDUCT', 'AUDITOR_BEHAVIOR', 'CERTIFICATION_DECISION', 'CERTIFICATE_MISUSE', 'OTHER');

-- CreateEnum
CREATE TYPE "ComplaintStatus" AS ENUM ('RECEIVED', 'UNDER_INVESTIGATION', 'RESOLVED', 'CLOSED', 'ESCALATED');

-- CreateEnum
CREATE TYPE "CertDecisionType" AS ENUM ('GRANT', 'REFUSE', 'SUSPEND', 'WITHDRAW', 'SPECIAL_AUDIT');

-- CreateEnum
CREATE TYPE "AppealStatus" AS ENUM ('RECEIVED', 'PANEL_REVIEW', 'DECIDED', 'CLOSED');

-- CreateEnum
CREATE TYPE "AppealPanelDecision" AS ENUM ('UPHELD', 'REJECTED', 'PARTIALLY_UPHELD');

-- CreateEnum
CREATE TYPE "TechnicalReviewStatus" AS ENUM ('PENDING', 'APPROVED', 'REQUIRES_CLARIFICATION', 'REJECTED');

-- CreateTable
CREATE TABLE "CbOrg" (
    "id" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "code" TEXT NOT NULL,
    "isActive" BOOLEAN NOT NULL DEFAULT true,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "CbOrg_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "User" (
    "id" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "email" TEXT NOT NULL,
    "passwordHash" TEXT NOT NULL,
    "role" "Role" NOT NULL,
    "isActive" BOOLEAN NOT NULL DEFAULT true,
    "cbOrgId" TEXT,
    "clientOrgId" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "User_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "ClientOrg" (
    "id" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "registeredId" TEXT NOT NULL DEFAULT '',
    "registeredAddress" TEXT NOT NULL,
    "customerId" TEXT NOT NULL,
    "totalEmployeeCount" INTEGER NOT NULL,
    "contactTelephone" TEXT NOT NULL DEFAULT '',
    "contactFax" TEXT NOT NULL DEFAULT '',
    "contactEmail" TEXT NOT NULL DEFAULT '',
    "contactWebsite" TEXT NOT NULL DEFAULT '',
    "signatoryName" TEXT NOT NULL DEFAULT '',
    "signatoryTitle" TEXT NOT NULL DEFAULT '',
    "msRepresentativeName" TEXT NOT NULL DEFAULT '',
    "msRepresentativeTitle" TEXT NOT NULL DEFAULT '',
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "ClientOrg_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Site" (
    "id" TEXT NOT NULL,
    "clientOrgId" TEXT NOT NULL,
    "siteName" TEXT NOT NULL,
    "siteAddress" TEXT NOT NULL,
    "siteEmployeeCount" INTEGER,
    "siteScope" TEXT NOT NULL DEFAULT '',
    "active" BOOLEAN NOT NULL DEFAULT true,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "Site_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Standard" (
    "id" TEXT NOT NULL,
    "code" TEXT NOT NULL,
    "title" TEXT NOT NULL,
    "naceCode" TEXT NOT NULL DEFAULT '',
    "eaCode" TEXT NOT NULL DEFAULT '',
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "Standard_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Certification" (
    "id" TEXT NOT NULL,
    "clientOrgId" TEXT NOT NULL,
    "standardId" TEXT NOT NULL,
    "certificationScope" TEXT NOT NULL,
    "certificateId" TEXT NOT NULL DEFAULT '',
    "certificateStatus" "CertificateStatus" NOT NULL DEFAULT 'DRAFT',
    "issueDate" TIMESTAMP(3),
    "expiryDate" TIMESTAMP(3),
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "Certification_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "CertificateHistory" (
    "id" TEXT NOT NULL,
    "certificationId" TEXT NOT NULL,
    "action" "CertHistoryAction" NOT NULL,
    "actionDate" TIMESTAMP(3) NOT NULL,
    "relatedAuditId" TEXT,
    "relatedDecisionId" TEXT,
    "certificateNumberSnapshot" TEXT NOT NULL DEFAULT '',
    "certificationScopeSnapshot" TEXT NOT NULL DEFAULT '',
    "validFrom" TIMESTAMP(3),
    "validTo" TIMESTAMP(3),
    "actionById" TEXT,
    "actionReason" TEXT NOT NULL DEFAULT '',
    "internalNotes" TEXT NOT NULL DEFAULT '',
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "CertificateHistory_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "SurveillanceSchedule" (
    "id" TEXT NOT NULL,
    "certificationId" TEXT NOT NULL,
    "cycleStart" TIMESTAMP(3) NOT NULL,
    "cycleEnd" TIMESTAMP(3) NOT NULL,
    "surveillance1DueDate" TIMESTAMP(3) NOT NULL,
    "surveillance2DueDate" TIMESTAMP(3) NOT NULL,
    "recertificationDueDate" TIMESTAMP(3) NOT NULL,
    "surveillance1AuditId" TEXT,
    "surveillance2AuditId" TEXT,
    "recertificationAuditId" TEXT,

    CONSTRAINT "SurveillanceSchedule_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "AuditProgram" (
    "id" TEXT NOT NULL,
    "clientOrgId" TEXT NOT NULL,
    "title" TEXT NOT NULL,
    "year" INTEGER NOT NULL,
    "status" "AuditProgramStatus" NOT NULL DEFAULT 'DRAFT',
    "objectives" TEXT NOT NULL,
    "risksOpportunities" TEXT NOT NULL,
    "createdById" TEXT NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "AuditProgram_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Audit" (
    "id" TEXT NOT NULL,
    "programId" TEXT,
    "clientOrgId" TEXT NOT NULL,
    "auditType" "AuditType" NOT NULL,
    "dateFrom" TIMESTAMP(3) NOT NULL,
    "dateTo" TIMESTAMP(3) NOT NULL,
    "plannedDurationHours" DOUBLE PRECISION,
    "actualDurationHours" DOUBLE PRECISION,
    "durationJustification" TEXT NOT NULL DEFAULT '',
    "status" "AuditStatus" NOT NULL DEFAULT 'DRAFT',
    "createdById" TEXT NOT NULL,
    "leadAuditorId" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "Audit_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "AuditCertification" (
    "auditId" TEXT NOT NULL,
    "certificationId" TEXT NOT NULL,

    CONSTRAINT "AuditCertification_pkey" PRIMARY KEY ("auditId","certificationId")
);

-- CreateTable
CREATE TABLE "AuditSite" (
    "auditId" TEXT NOT NULL,
    "siteId" TEXT NOT NULL,

    CONSTRAINT "AuditSite_pkey" PRIMARY KEY ("auditId","siteId")
);

-- CreateTable
CREATE TABLE "AuditTeamMember" (
    "id" TEXT NOT NULL,
    "auditId" TEXT NOT NULL,
    "userId" TEXT,
    "name" TEXT NOT NULL,
    "title" TEXT NOT NULL DEFAULT '',
    "role" "TeamMemberRole" NOT NULL,
    "dateFrom" TIMESTAMP(3) NOT NULL,
    "dateTo" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "AuditTeamMember_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "AuditChanges" (
    "id" TEXT NOT NULL,
    "auditId" TEXT NOT NULL,
    "changeOfName" BOOLEAN NOT NULL DEFAULT false,
    "changeOfScope" BOOLEAN NOT NULL DEFAULT false,
    "changeOfSites" BOOLEAN NOT NULL DEFAULT false,
    "changeOfMsRep" BOOLEAN NOT NULL DEFAULT false,
    "changeOfSignatory" BOOLEAN NOT NULL DEFAULT false,
    "changeOfEmployeeCount" BOOLEAN NOT NULL DEFAULT false,
    "changeOfContactInfo" BOOLEAN NOT NULL DEFAULT false,
    "otherHasChange" BOOLEAN NOT NULL DEFAULT false,
    "otherDescription" TEXT NOT NULL DEFAULT '',

    CONSTRAINT "AuditChanges_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "AuditPlanReview" (
    "id" TEXT NOT NULL,
    "auditId" TEXT NOT NULL,
    "deviationsYesNo" BOOLEAN NOT NULL DEFAULT false,
    "deviationsDetails" TEXT NOT NULL DEFAULT '',
    "issuesAffectingYesNo" BOOLEAN NOT NULL DEFAULT false,
    "issuesAffectingDetails" TEXT NOT NULL DEFAULT '',
    "nextAuditDateFrom" TIMESTAMP(3),
    "nextAuditDateTo" TIMESTAMP(3),

    CONSTRAINT "AuditPlanReview_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "AuditSummary" (
    "id" TEXT NOT NULL,
    "auditId" TEXT NOT NULL,
    "objectivesMet" BOOLEAN NOT NULL DEFAULT false,
    "objectivesComments" TEXT NOT NULL DEFAULT '',
    "scopeAppropriate" BOOLEAN NOT NULL DEFAULT false,
    "scopeComments" TEXT NOT NULL DEFAULT '',
    "msMeetsRequirements" BOOLEAN NOT NULL DEFAULT false,
    "msComments" TEXT NOT NULL DEFAULT '',
    "managementReviewEffective" BOOLEAN NOT NULL DEFAULT false,
    "managementReviewComments" TEXT NOT NULL DEFAULT '',
    "internalAuditEffective" BOOLEAN NOT NULL DEFAULT false,
    "internalAuditComments" TEXT NOT NULL DEFAULT '',
    "msEffective" BOOLEAN NOT NULL DEFAULT false,
    "msEffectiveComments" TEXT NOT NULL DEFAULT '',
    "correctUseOfLogos" BOOLEAN NOT NULL DEFAULT false,
    "logosComments" TEXT NOT NULL DEFAULT '',
    "promotedToCommittee" BOOLEAN NOT NULL DEFAULT false,
    "committeeComments" TEXT NOT NULL DEFAULT '',
    "generalCommentary" TEXT NOT NULL DEFAULT '',

    CONSTRAINT "AuditSummary_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Finding" (
    "id" TEXT NOT NULL,
    "auditId" TEXT NOT NULL,
    "standardId" TEXT,
    "clause" TEXT NOT NULL,
    "siteId" TEXT,
    "findingType" "FindingType" NOT NULL,
    "createdById" TEXT NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "objectiveEvidence" TEXT,
    "statementOfNc" TEXT,
    "auditorExplanation" TEXT,
    "clientRootCause" TEXT NOT NULL DEFAULT '',
    "clientCorrection" TEXT NOT NULL DEFAULT '',
    "clientCorrectiveAction" TEXT NOT NULL DEFAULT '',
    "dueDate" TIMESTAMP(3),
    "verificationStatus" "NCVerificationStatus" NOT NULL DEFAULT 'OPEN',
    "verifiedById" TEXT,
    "verifiedAt" TIMESTAMP(3),
    "verificationNotes" TEXT NOT NULL DEFAULT '',
    "observationStatement" TEXT,
    "observationExplanation" TEXT NOT NULL DEFAULT '',
    "ofiDescription" TEXT,

    CONSTRAINT "Finding_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "AuditRecommendation" (
    "id" TEXT NOT NULL,
    "auditId" TEXT NOT NULL,
    "recommendation" TEXT NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "AuditRecommendation_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "AuditStatusLog" (
    "id" TEXT NOT NULL,
    "auditId" TEXT NOT NULL,
    "fromStatus" "AuditStatus",
    "toStatus" "AuditStatus" NOT NULL,
    "changedById" TEXT NOT NULL,
    "notes" TEXT NOT NULL DEFAULT '',
    "changedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "AuditStatusLog_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "EvidenceFile" (
    "id" TEXT NOT NULL,
    "auditId" TEXT NOT NULL,
    "fileName" TEXT NOT NULL,
    "filePath" TEXT NOT NULL,
    "mimeType" TEXT NOT NULL,
    "sizeBytes" INTEGER NOT NULL,
    "uploadedById" TEXT NOT NULL,
    "uploadedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "EvidenceFile_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "AuditorCompetenceWarning" (
    "id" TEXT NOT NULL,
    "userId" TEXT NOT NULL,
    "description" TEXT NOT NULL,
    "raisedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "AuditorCompetenceWarning_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Complaint" (
    "id" TEXT NOT NULL,
    "complaintNumber" TEXT NOT NULL,
    "clientOrgId" TEXT,
    "relatedAuditId" TEXT,
    "complainantName" TEXT NOT NULL,
    "complainantEmail" TEXT NOT NULL DEFAULT '',
    "complaintType" "ComplaintType" NOT NULL,
    "description" TEXT NOT NULL,
    "submittedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "submittedById" TEXT,
    "status" "ComplaintStatus" NOT NULL DEFAULT 'RECEIVED',
    "assignedInvestigatorId" TEXT,
    "investigationStartedAt" TIMESTAMP(3),
    "investigationNotes" TEXT NOT NULL DEFAULT '',
    "investigationCompletedAt" TIMESTAMP(3),
    "resolutionDetails" TEXT NOT NULL DEFAULT '',
    "correctiveActions" TEXT NOT NULL DEFAULT '',

    CONSTRAINT "Complaint_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "CertificationDecision" (
    "id" TEXT NOT NULL,
    "auditId" TEXT NOT NULL,
    "decisionMakerId" TEXT NOT NULL,
    "decidedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "decision" "CertDecisionType" NOT NULL,
    "decisionNotes" TEXT NOT NULL,

    CONSTRAINT "CertificationDecision_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "CertificationDecisionCert" (
    "decisionId" TEXT NOT NULL,
    "certificationId" TEXT NOT NULL,

    CONSTRAINT "CertificationDecisionCert_pkey" PRIMARY KEY ("decisionId","certificationId")
);

-- CreateTable
CREATE TABLE "Appeal" (
    "id" TEXT NOT NULL,
    "appealNumber" TEXT NOT NULL,
    "relatedComplaintId" TEXT,
    "relatedDecisionId" TEXT,
    "appellantName" TEXT NOT NULL,
    "appellantEmail" TEXT NOT NULL DEFAULT '',
    "grounds" TEXT NOT NULL,
    "submittedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "submittedById" TEXT,
    "status" "AppealStatus" NOT NULL DEFAULT 'RECEIVED',
    "panelDecision" "AppealPanelDecision",
    "panelDecisionDate" TIMESTAMP(3),
    "panelJustification" TEXT NOT NULL DEFAULT '',

    CONSTRAINT "Appeal_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "TechnicalReview" (
    "id" TEXT NOT NULL,
    "auditId" TEXT NOT NULL,
    "reviewerId" TEXT NOT NULL,
    "reviewedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "status" "TechnicalReviewStatus" NOT NULL DEFAULT 'PENDING',
    "scopeVerified" BOOLEAN NOT NULL DEFAULT false,
    "objectivesVerified" BOOLEAN NOT NULL DEFAULT false,
    "findingsReviewed" BOOLEAN NOT NULL DEFAULT false,
    "conclusionClear" BOOLEAN NOT NULL DEFAULT false,
    "reviewerNotes" TEXT NOT NULL DEFAULT '',
    "clarificationRequested" TEXT NOT NULL DEFAULT '',

    CONSTRAINT "TechnicalReview_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "CbOrg_code_key" ON "CbOrg"("code");

-- CreateIndex
CREATE UNIQUE INDEX "User_email_key" ON "User"("email");

-- CreateIndex
CREATE UNIQUE INDEX "ClientOrg_customerId_key" ON "ClientOrg"("customerId");

-- CreateIndex
CREATE UNIQUE INDEX "Standard_code_key" ON "Standard"("code");

-- CreateIndex
CREATE UNIQUE INDEX "Certification_clientOrgId_standardId_key" ON "Certification"("clientOrgId", "standardId");

-- CreateIndex
CREATE INDEX "CertificateHistory_action_idx" ON "CertificateHistory"("action");

-- CreateIndex
CREATE INDEX "CertificateHistory_actionDate_idx" ON "CertificateHistory"("actionDate");

-- CreateIndex
CREATE UNIQUE INDEX "SurveillanceSchedule_certificationId_key" ON "SurveillanceSchedule"("certificationId");

-- CreateIndex
CREATE UNIQUE INDEX "AuditProgram_clientOrgId_year_title_key" ON "AuditProgram"("clientOrgId", "year", "title");

-- CreateIndex
CREATE INDEX "Audit_status_idx" ON "Audit"("status");

-- CreateIndex
CREATE INDEX "Audit_clientOrgId_status_idx" ON "Audit"("clientOrgId", "status");

-- CreateIndex
CREATE INDEX "Audit_leadAuditorId_idx" ON "Audit"("leadAuditorId");

-- CreateIndex
CREATE UNIQUE INDEX "AuditChanges_auditId_key" ON "AuditChanges"("auditId");

-- CreateIndex
CREATE UNIQUE INDEX "AuditPlanReview_auditId_key" ON "AuditPlanReview"("auditId");

-- CreateIndex
CREATE UNIQUE INDEX "AuditSummary_auditId_key" ON "AuditSummary"("auditId");

-- CreateIndex
CREATE INDEX "Finding_auditId_idx" ON "Finding"("auditId");

-- CreateIndex
CREATE INDEX "Finding_findingType_idx" ON "Finding"("findingType");

-- CreateIndex
CREATE INDEX "Finding_verificationStatus_idx" ON "Finding"("verificationStatus");

-- CreateIndex
CREATE INDEX "AuditStatusLog_auditId_idx" ON "AuditStatusLog"("auditId");

-- CreateIndex
CREATE INDEX "EvidenceFile_auditId_idx" ON "EvidenceFile"("auditId");

-- CreateIndex
CREATE UNIQUE INDEX "Complaint_complaintNumber_key" ON "Complaint"("complaintNumber");

-- CreateIndex
CREATE INDEX "Complaint_status_idx" ON "Complaint"("status");

-- CreateIndex
CREATE INDEX "Complaint_complaintNumber_idx" ON "Complaint"("complaintNumber");

-- CreateIndex
CREATE UNIQUE INDEX "CertificationDecision_auditId_key" ON "CertificationDecision"("auditId");

-- CreateIndex
CREATE UNIQUE INDEX "Appeal_appealNumber_key" ON "Appeal"("appealNumber");

-- CreateIndex
CREATE INDEX "Appeal_status_idx" ON "Appeal"("status");

-- CreateIndex
CREATE INDEX "Appeal_appealNumber_idx" ON "Appeal"("appealNumber");

-- CreateIndex
CREATE UNIQUE INDEX "TechnicalReview_auditId_key" ON "TechnicalReview"("auditId");

-- AddForeignKey
ALTER TABLE "User" ADD CONSTRAINT "User_cbOrgId_fkey" FOREIGN KEY ("cbOrgId") REFERENCES "CbOrg"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "User" ADD CONSTRAINT "User_clientOrgId_fkey" FOREIGN KEY ("clientOrgId") REFERENCES "ClientOrg"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Site" ADD CONSTRAINT "Site_clientOrgId_fkey" FOREIGN KEY ("clientOrgId") REFERENCES "ClientOrg"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Certification" ADD CONSTRAINT "Certification_clientOrgId_fkey" FOREIGN KEY ("clientOrgId") REFERENCES "ClientOrg"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Certification" ADD CONSTRAINT "Certification_standardId_fkey" FOREIGN KEY ("standardId") REFERENCES "Standard"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "CertificateHistory" ADD CONSTRAINT "CertificateHistory_certificationId_fkey" FOREIGN KEY ("certificationId") REFERENCES "Certification"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "CertificateHistory" ADD CONSTRAINT "CertificateHistory_actionById_fkey" FOREIGN KEY ("actionById") REFERENCES "User"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "SurveillanceSchedule" ADD CONSTRAINT "SurveillanceSchedule_certificationId_fkey" FOREIGN KEY ("certificationId") REFERENCES "Certification"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "AuditProgram" ADD CONSTRAINT "AuditProgram_clientOrgId_fkey" FOREIGN KEY ("clientOrgId") REFERENCES "ClientOrg"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "AuditProgram" ADD CONSTRAINT "AuditProgram_createdById_fkey" FOREIGN KEY ("createdById") REFERENCES "User"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Audit" ADD CONSTRAINT "Audit_programId_fkey" FOREIGN KEY ("programId") REFERENCES "AuditProgram"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Audit" ADD CONSTRAINT "Audit_clientOrgId_fkey" FOREIGN KEY ("clientOrgId") REFERENCES "ClientOrg"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Audit" ADD CONSTRAINT "Audit_createdById_fkey" FOREIGN KEY ("createdById") REFERENCES "User"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Audit" ADD CONSTRAINT "Audit_leadAuditorId_fkey" FOREIGN KEY ("leadAuditorId") REFERENCES "User"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "AuditCertification" ADD CONSTRAINT "AuditCertification_auditId_fkey" FOREIGN KEY ("auditId") REFERENCES "Audit"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "AuditCertification" ADD CONSTRAINT "AuditCertification_certificationId_fkey" FOREIGN KEY ("certificationId") REFERENCES "Certification"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "AuditSite" ADD CONSTRAINT "AuditSite_auditId_fkey" FOREIGN KEY ("auditId") REFERENCES "Audit"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "AuditSite" ADD CONSTRAINT "AuditSite_siteId_fkey" FOREIGN KEY ("siteId") REFERENCES "Site"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "AuditTeamMember" ADD CONSTRAINT "AuditTeamMember_auditId_fkey" FOREIGN KEY ("auditId") REFERENCES "Audit"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "AuditTeamMember" ADD CONSTRAINT "AuditTeamMember_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "AuditChanges" ADD CONSTRAINT "AuditChanges_auditId_fkey" FOREIGN KEY ("auditId") REFERENCES "Audit"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "AuditPlanReview" ADD CONSTRAINT "AuditPlanReview_auditId_fkey" FOREIGN KEY ("auditId") REFERENCES "Audit"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "AuditSummary" ADD CONSTRAINT "AuditSummary_auditId_fkey" FOREIGN KEY ("auditId") REFERENCES "Audit"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Finding" ADD CONSTRAINT "Finding_auditId_fkey" FOREIGN KEY ("auditId") REFERENCES "Audit"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Finding" ADD CONSTRAINT "Finding_standardId_fkey" FOREIGN KEY ("standardId") REFERENCES "Standard"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Finding" ADD CONSTRAINT "Finding_siteId_fkey" FOREIGN KEY ("siteId") REFERENCES "Site"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Finding" ADD CONSTRAINT "Finding_createdById_fkey" FOREIGN KEY ("createdById") REFERENCES "User"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Finding" ADD CONSTRAINT "Finding_verifiedById_fkey" FOREIGN KEY ("verifiedById") REFERENCES "User"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "AuditRecommendation" ADD CONSTRAINT "AuditRecommendation_auditId_fkey" FOREIGN KEY ("auditId") REFERENCES "Audit"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "AuditStatusLog" ADD CONSTRAINT "AuditStatusLog_auditId_fkey" FOREIGN KEY ("auditId") REFERENCES "Audit"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "AuditStatusLog" ADD CONSTRAINT "AuditStatusLog_changedById_fkey" FOREIGN KEY ("changedById") REFERENCES "User"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "EvidenceFile" ADD CONSTRAINT "EvidenceFile_auditId_fkey" FOREIGN KEY ("auditId") REFERENCES "Audit"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "EvidenceFile" ADD CONSTRAINT "EvidenceFile_uploadedById_fkey" FOREIGN KEY ("uploadedById") REFERENCES "User"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "AuditorCompetenceWarning" ADD CONSTRAINT "AuditorCompetenceWarning_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Complaint" ADD CONSTRAINT "Complaint_clientOrgId_fkey" FOREIGN KEY ("clientOrgId") REFERENCES "ClientOrg"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Complaint" ADD CONSTRAINT "Complaint_relatedAuditId_fkey" FOREIGN KEY ("relatedAuditId") REFERENCES "Audit"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Complaint" ADD CONSTRAINT "Complaint_submittedById_fkey" FOREIGN KEY ("submittedById") REFERENCES "User"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Complaint" ADD CONSTRAINT "Complaint_assignedInvestigatorId_fkey" FOREIGN KEY ("assignedInvestigatorId") REFERENCES "User"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "CertificationDecision" ADD CONSTRAINT "CertificationDecision_auditId_fkey" FOREIGN KEY ("auditId") REFERENCES "Audit"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "CertificationDecision" ADD CONSTRAINT "CertificationDecision_decisionMakerId_fkey" FOREIGN KEY ("decisionMakerId") REFERENCES "User"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "CertificationDecisionCert" ADD CONSTRAINT "CertificationDecisionCert_decisionId_fkey" FOREIGN KEY ("decisionId") REFERENCES "CertificationDecision"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "CertificationDecisionCert" ADD CONSTRAINT "CertificationDecisionCert_certificationId_fkey" FOREIGN KEY ("certificationId") REFERENCES "Certification"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Appeal" ADD CONSTRAINT "Appeal_relatedComplaintId_fkey" FOREIGN KEY ("relatedComplaintId") REFERENCES "Complaint"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Appeal" ADD CONSTRAINT "Appeal_relatedDecisionId_fkey" FOREIGN KEY ("relatedDecisionId") REFERENCES "CertificationDecision"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Appeal" ADD CONSTRAINT "Appeal_submittedById_fkey" FOREIGN KEY ("submittedById") REFERENCES "User"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "TechnicalReview" ADD CONSTRAINT "TechnicalReview_auditId_fkey" FOREIGN KEY ("auditId") REFERENCES "Audit"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "TechnicalReview" ADD CONSTRAINT "TechnicalReview_reviewerId_fkey" FOREIGN KEY ("reviewerId") REFERENCES "User"("id") ON DELETE RESTRICT ON UPDATE CASCADE;
