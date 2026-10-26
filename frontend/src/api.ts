import axios from 'axios'
export const api = axios.create({ baseURL: '/api' })
export type PatientInput = { full_name: string; date_of_birth: string; email: string; glucose: string; haemoglobin: string; cholesterol: string }
export type Patient = Omit<PatientInput, 'glucose' | 'haemoglobin' | 'cholesterol'> & { id: number; glucose: number; haemoglobin: number; cholesterol: number; ai_remarks: string | null; ai_status: 'pending' | 'completed' | 'failed'; created_at: string; updated_at: string }
export function errorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const data = error.response?.data
    if (Array.isArray(data?.errors)) return data.errors.map((item: {field: string; message: string; input: unknown}) => `${item.field}: ${item.message} (input: ${JSON.stringify(item.input)})`).join('; ')
    if (typeof data?.detail === 'string') return data.detail
  }
  return 'Request failed. Check that the backend is running.'
}
export function displayDate(iso: string): string { const [y,m,d] = iso.split('-'); return `${d}/${m}/${y}` }
