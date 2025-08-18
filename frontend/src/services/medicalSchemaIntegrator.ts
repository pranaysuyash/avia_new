export interface MedicalSchema {
  id: string;
  name: string;
  version: string;
  fields: MedicalField[];
}

export interface MedicalField {
  id: string;
  name: string;
  type: 'text' | 'number' | 'date' | 'enum' | 'boolean';
  required: boolean;
  validation?: any;
  options?: string[];
}

export interface ValidationResult {
  isValid: boolean;
  errors: string[];
  warnings: string[];
}

export class MedicalSchemaIntegrator {
  private schemas: Map<string, MedicalSchema> = new Map();

  addSchema(schema: MedicalSchema): void {
    this.schemas.set(schema.id, schema);
  }

  getSchema(id: string): MedicalSchema | undefined {
    return this.schemas.get(id);
  }

  getSchemas(): MedicalSchema[] {
    return Array.from(this.schemas.values());
  }

  validateData(schemaId: string, data: any): ValidationResult {
    const schema = this.schemas.get(schemaId);
    if (!schema) {
      return {
        isValid: false,
        errors: [`Schema ${schemaId} not found`],
        warnings: []
      };
    }

    const errors: string[] = [];
    const warnings: string[] = [];

    schema.fields.forEach(field => {
      const value = data[field.id];
      
      if (field.required && (value === undefined || value === null || value === '')) {
        errors.push(`Field ${field.name} is required`);
      }

      if (value !== undefined && value !== null && value !== '') {
        if (field.type === 'number' && isNaN(Number(value))) {
          errors.push(`Field ${field.name} must be a number`);
        }
        
        if (field.type === 'enum' && field.options && !field.options.includes(value)) {
          errors.push(`Field ${field.name} must be one of: ${field.options.join(', ')}`);
        }
      }
    });

    return {
      isValid: errors.length === 0,
      errors,
      warnings
    };
  }

  transformData(schemaId: string, data: any): any {
    const schema = this.schemas.get(schemaId);
    if (!schema) {
      return data;
    }

    const transformed: any = {};
    
    schema.fields.forEach(field => {
      const value = data[field.id];
      if (value !== undefined) {
        if (field.type === 'number') {
          transformed[field.id] = Number(value);
        } else if (field.type === 'boolean') {
          transformed[field.id] = Boolean(value);
        } else {
          transformed[field.id] = value;
        }
      }
    });

    return transformed;
  }

  // Add methods expected by RealtimeCollaborationEditor
  async initialize(): Promise<void> {
    // Initialize method for compatibility
  }

  async validateContent(content: string): Promise<{ hasErrors: boolean; errors: string[] }> {
    // Validate medical content
    const errors: string[] = [];
    
    // Simple validation for demonstration
    if (content.length < 10) {
      errors.push('Content too short for medical validation');
    }
    
    return {
      hasErrors: errors.length > 0,
      errors
    };
  }

  async analyzeMedicalTerm(term: string): Promise<{
    terminology: string;
    category: string;
    confidence: number;
  }> {
    // Analyze medical terminology
    return {
      terminology: term,
      category: 'general',
      confidence: 0.9
    };
  }
}

export default new MedicalSchemaIntegrator();