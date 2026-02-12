import { useState, useEffect, useRef } from 'react'
import { useForm } from 'react-hook-form'
import { z } from 'zod'
import { zodResolver } from '@hookform/resolvers/zod'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { useTheme } from '@/components/theme-provider'
import { ErrorState } from '@/components/feedback-state'
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from '@/components/ui/form'
import { FormActions } from '@/components/forms/FormActions'
import { FormSection } from '@/components/forms/FormSection'
import { toast } from 'sonner'

const PERFIL_KEY = 'escalaflow-perfil'
const MAX_IMAGE_BYTES = 1_500_000 // ~1.5MB

type PerfilData = {
  nome: string
  fotoBase64: string
  tema?: 'light' | 'dark' | 'system'
}

function loadPerfil(): PerfilData {
  try {
    const s = localStorage.getItem(PERFIL_KEY)
    if (s) return JSON.parse(s)
  } catch {
    // Keep fallback defaults when localStorage is unavailable or corrupted.
  }
  return { nome: 'Usuário', fotoBase64: '', tema: 'system' }
}

function savePerfil(data: PerfilData): boolean {
  try {
    localStorage.setItem(PERFIL_KEY, JSON.stringify(data))
    return true
  } catch {
    return false
  }
}

export function PerfilPage() {
  const { theme, setTheme } = useTheme()
  const [perfil, setPerfil] = useState<PerfilData>(loadPerfil)
  const [storageError, setStorageError] = useState<string | null>(null)
  const fileRef = useRef<HTMLInputElement>(null)
  const formSchema = z.object({
    nome: z.string().trim().min(2, 'Informe ao menos 2 caracteres para o nome.'),
    tema: z.enum(['light', 'dark', 'system']),
  })
  type ProfileForm = z.infer<typeof formSchema>
  const form = useForm<ProfileForm>({
    resolver: zodResolver(formSchema),
    defaultValues: { nome: perfil.nome, tema: (perfil.tema || theme) as 'light' | 'dark' | 'system' },
  })

  useEffect(() => {
    form.reset({ nome: perfil.nome, tema: (perfil.tema || theme) as 'light' | 'dark' | 'system' })
  }, [perfil, theme, form])

  const handleFotoChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file || !file.type.startsWith('image/')) return
    if (file.size > MAX_IMAGE_BYTES) {
      setStorageError('Imagem muito grande. Use uma foto menor que 1.5MB.')
      toast.error('Imagem muito grande. Use uma foto menor que 1.5MB.')
      return
    }
    const reader = new FileReader()
    reader.onload = () => {
      const result = reader.result as string
      setPerfil((p) => ({ ...p, fotoBase64: result }))
    }
    reader.readAsDataURL(file)
  }

  const handleSaveProfile = async (values: ProfileForm) => {
    const next: PerfilData = { ...perfil, nome: values.nome, tema: values.tema }
    const ok = savePerfil(next)
    if (!ok) {
      setStorageError('Não foi possível salvar o perfil local. Reduza a foto e tente novamente.')
      toast.error('Falha ao salvar perfil local.')
      return
    }
    setStorageError(null)
    setPerfil(next)
    setTheme(values.tema)
    toast.success('Perfil atualizado com sucesso.')
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold tracking-tight text-foreground">Perfil</h1>
      {storageError && <ErrorState message={storageError} />}

      <Card>
        <CardHeader>
          <CardTitle>Configurações pessoais</CardTitle>
          <CardDescription>Gerencie nome, foto e preferências de tema desta instalação local.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="flex items-center gap-6">
            <div className="relative">
              <Avatar className="h-24 w-24">
                <AvatarImage src={perfil.fotoBase64} alt={perfil.nome} />
                <AvatarFallback className="text-2xl">
                  {perfil.nome
                    .split(' ')
                    .map((n) => n[0])
                    .filter(Boolean)
                    .slice(0, 2)
                    .join('')
                    .toUpperCase() || 'U'}
                </AvatarFallback>
              </Avatar>
              <input
                ref={fileRef}
                type="file"
                accept="image/*"
                className="hidden"
                onChange={handleFotoChange}
              />
              <Button
                variant="outline"
                size="sm"
                className="absolute -bottom-2 left-1/2 -translate-x-1/2"
                onClick={() => fileRef.current?.click()}
              >
                Alterar foto
              </Button>
            </div>
            <div className="flex-1 space-y-4">
              <Form {...form}>
                <form onSubmit={form.handleSubmit(handleSaveProfile)} className="space-y-4">
                  <FormField
                    control={form.control}
                    name="nome"
                    render={({ field }) => (
                      <FormItem>
                        <FormSection>
                          <FormLabel>Nome</FormLabel>
                          <FormControl>
                            <Input placeholder="Seu nome" {...field} />
                          </FormControl>
                        </FormSection>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                  <FormField
                    control={form.control}
                    name="tema"
                    render={({ field }) => (
                      <FormItem>
                        <FormSection>
                          <FormLabel>Tema</FormLabel>
                          <Select value={field.value} onValueChange={field.onChange}>
                            <FormControl>
                              <SelectTrigger className="w-[180px]">
                                <SelectValue />
                              </SelectTrigger>
                            </FormControl>
                            <SelectContent>
                              <SelectItem value="light">Claro</SelectItem>
                              <SelectItem value="dark">Escuro</SelectItem>
                              <SelectItem value="system">Sistema</SelectItem>
                            </SelectContent>
                          </Select>
                        </FormSection>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                  <FormActions isSubmitting={form.formState.isSubmitting} submitLabel="Salvar perfil" />
                </form>
              </Form>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
