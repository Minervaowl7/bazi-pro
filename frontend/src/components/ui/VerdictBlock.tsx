interface VerdictBlockProps {
  children: React.ReactNode;
  className?: string;
}

export function VerdictBlock({ children, className = "" }: VerdictBlockProps) {
  return (
    <div className={`verdict-block ${className}`.trim()}>
      {children}
    </div>
  );
}
