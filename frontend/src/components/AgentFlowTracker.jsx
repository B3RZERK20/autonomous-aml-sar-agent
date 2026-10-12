import React from 'react';
import { Database, BookOpen, FileText, CheckCircle2, ArrowRight } from 'lucide-react';

export default function AgentFlowTracker({ activeStep }) {
  const steps = [
    {
      id: 1,
      name: 'Data Gatherer',
      role: 'MCP Database & Sanctions Watchlist',
      icon: Database,
    },
    {
      id: 2,
      name: 'Compliance Analyst',
      role: 'FinCEN BSA & FATF RAG Engine',
      icon: BookOpen,
    },
    {
      id: 3,
      name: 'SAR Writer',
      role: 'BSA Form 111 Narrative Generator',
      icon: FileText,
    },
    {
      id: 4,
      name: 'Evaluator Guardrail',
      role: 'Hallucination & Math Verification',
      icon: CheckCircle2,
    },
  ];

  return (
    <div className="flow-tracker-card">
      <div className="flow-steps-row">
        {steps.map((step, idx) => {
          const Icon = step.icon;
          const isActive = activeStep === step.id;
          const isDone = activeStep > step.id || activeStep === 5;

          let stepClass = 'flow-step';
          if (isActive) stepClass += ' active';
          if (isDone) stepClass += ' done';

          return (
            <React.Fragment key={step.id}>
              <div className={stepClass}>
                <div className="step-icon-wrap">
                  <Icon size={20} />
                </div>
                <div className="step-content">
                  <div className="step-name">
                    <span className="step-num">Node {step.id}:</span> {step.name}
                  </div>
                  <div className="step-role">{step.role}</div>
                </div>
              </div>
              {idx < steps.length - 1 && (
                <div className={`step-separator ${activeStep > step.id ? 'done' : ''}`}>
                  <ArrowRight size={18} />
                </div>
              )}
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
}
