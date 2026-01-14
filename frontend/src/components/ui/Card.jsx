// frontend/src/components/ui/Card.jsx
export const Card = ({ children, className = '', ...props }) => {
  return (
    <div 
      className={`bg-white dark:bg-dark-card rounded-lg shadow-sm border border-gray-200 dark:border-dark-border transition-colors duration-300 ${className}`}
      {...props}
    >
      {children}
    </div>
  );
};

export const CardHeader = ({ children, className = '' }) => {
  return (
    <div className={`px-6 py-4 border-b border-gray-200 dark:border-dark-border ${className}`}>
      {children}
    </div>
  );
};

export const CardBody = ({ children, className = '' }) => {
  return (
    <div className={`px-6 py-4 text-gray-900 dark:text-dark-text ${className}`}>
      {children}
    </div>
  );
};

export const CardFooter = ({ children, className = '' }) => {
  return (
    <div className={`px-6 py-4 border-t border-gray-200 dark:border-dark-border ${className}`}>
      {children}
    </div>
  );
};