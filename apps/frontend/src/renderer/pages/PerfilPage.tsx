import { useState, useEffect, useRef } from 'react'
import { useForm } from 'react-hook-form'
import { z } from 'zod'
import { zodResolver } from '@hookform/resolvers/zod'
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { ErrorState } from '@/components/feedback-state'
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from '@/components/ui/form'
import { FormActions } from '@/components/forms/FormActions'
import { FormSection } from '@/components/forms/FormSection'
import { toast } from 'sonner'

import { PERFIL_KEY, PERFIL_UPDATED_EVENT } from '@/lib/perfil'

const MAX_IMAGE_BYTES = 1_500_000 // ~1.5MB

type PerfilData = {
  nome: string
  organizacao: string
  fotoBase64: string
  tema?: 'light' | 'dark' | 'system'
}

function loadPerfil(): PerfilData {
  try {
    const s = localStorage.getItem(PERFIL_KEY)
    if (s) {
      const p = JSON.parse(s)
      return { nome: p.nome ?? 'Usuário', organizacao: p.organizacao ?? '', fotoBase64: p.fotoBase64 ?? '', tema: p.tema }
    }
  } catch {
    // Keep fallback defaults when localStorage is unavailable or corrupted.
  }
  return { nome: 'Usuário', organizacao: '', fotoBase64: '', tema: 'system' }
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
  const [perfil, setPerfil] = useState<PerfilData>(loadPerfil)
  const [storageError, setStorageError] = useState<string | null>(null)
  const fileRef = useRef<HTMLInputElement>(null)
  const formSchema = z.object({
    nome: z.string().trim().min(2, 'Informe ao menos 2 caracteres para o nome.'),
    organizacao: z.string().trim(),
  })
  type ProfileForm = z.infer<typeof formSchema>
  const form = useForm<ProfileForm>({
    resolver: zodResolver(formSchema),
    defaultValues: { nome: perfil.nome, organizacao: perfil.organizacao },
  })

  useEffect(() => {
    form.reset({ nome: perfil.nome, organizacao: perfil.organizacao })
  }, [perfil, form])

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
    const next: PerfilData = { ...perfil, nome: values.nome, organizacao: values.organizacao }
    const ok = savePerfil(next)
    if (!ok) {
      setStorageError('Não foi possível salvar o perfil local. Reduza a foto e tente novamente.')
      toast.error('Falha ao salvar perfil local.')
      return
    }
    setStorageError(null)
    setPerfil(next)
    window.dispatchEvent(new CustomEvent(PERFIL_UPDATED_EVENT))
    toast.success('Perfil atualizado com sucesso.')
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold tracking-tight text-foreground">Perfil</h1>
      {storageError && <ErrorState message={storageError} />}

      <Card>
        <CardHeader>
          <CardTitle>Configurações pessoais</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col gap-6 sm:flex-row sm:items-start">
            <div className="flex flex-col items-center gap-3 shrink-0">
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
                onClick={() => fileRef.current?.click()}
              >
                Alterar foto
              </Button>
            </div>
            <Form {...form}>
              <form id="perfil-form" onSubmit={form.handleSubmit(handleSaveProfile)} className="grid w-full gap-4 sm:grid-cols-2 flex-1 min-w-0">
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
                  name="organizacao"
                  render={({ field }) => (
                    <FormItem>
                      <FormSection>
                        <FormLabel>Organização</FormLabel>
                        <FormControl>
                          <Input placeholder="Nome da empresa ou unidade" {...field} />
                        </FormControl>
                      </FormSection>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </form>
            </Form>
          </div>
        </CardContent>
        <CardFooter className="border-t">
          <FormActions
            formId="perfil-form"
            isSubmitting={form.formState.isSubmitting}
            submitLabel="Salvar perfil"
          />
        </CardFooter>
      </Card>
    </div>
  )
}
