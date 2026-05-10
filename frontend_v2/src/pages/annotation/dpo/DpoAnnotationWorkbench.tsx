import React from 'react';
import DpoAnnotationPage from './DpoAnnotationPage';

export type DpoWorkbenchMode =
  | 'legacy'
  | 'pairwise'
  | 'best_of_n'
  | 'reference_choice'
  | 'multi_turn';

interface DpoAnnotationWorkbenchProps {
  mode: DpoWorkbenchMode;
}

const DpoAnnotationWorkbench: React.FC<DpoAnnotationWorkbenchProps> = ({ mode }) => {
  return <DpoAnnotationPage mode={mode} />;
};

export default DpoAnnotationWorkbench;
