import unittest
import test_company_session as fixtures
from models import PostagemChatDB, PostagemComentarioDB

class PostagemTests(unittest.TestCase):
    setUp = fixtures.CompanySessionTests.setUp
    tearDown = fixtures.CompanySessionTests.tearDown
    login = fixtures.CompanySessionTests.login

    def criar(self, **extra):
        return self.client.post('/postagem/criar-postagem', json={'conteudo_texto': '  Minha postagem 😀  ', **extra})

    def test_persistencia_autoria_comentarios(self):
        self.login()
        r = self.criar()
        self.assertEqual(r.status_code, 201, r.text)
        post = r.json()
        self.assertEqual(post['autor_id'], 1)
        self.assertEqual(post['conteudo_texto'], 'Minha postagem 😀')
        self.assertIsNone(post['midia_url'])
        self.login(2)
        comentario = self.client.post(f"/postagem/{post['id_post']}/comentarios", json={'texto': '  Olá!  '})
        self.assertEqual(comentario.status_code, 201, comentario.text)
        feed = self.client.get('/postagem')
        self.assertEqual(feed.headers['cache-control'], 'no-store')
        self.assertEqual(feed.json()[0]['comments'][0]['autorId'], 2)
        self.assertEqual(feed.json()[0]['comments'][0]['text'], 'Olá!')
        with self.sessions() as db:
            self.assertEqual(db.query(PostagemChatDB).count(), 1)
            self.assertEqual(db.query(PostagemComentarioDB).count(), 1)

    def test_validacao_e_autorizacao(self):
        self.assertEqual(self.criar().status_code, 401)
        self.assertEqual(self.client.get('/postagem').status_code, 401)
        self.login()
        for extra in ({'conteudo_texto': ' '}, {'conteudo_texto': 'x'*4001}, {'conteudo_texto': None},
                      {'midia_url': 'javascript:alert(1)'}, {'midia_url': 'https://user:pass@example.com/a'},
                      {'midia_url': 'https://example.com/'+'a'*240}, {'data_publicacao': '2000-01-01'},
                      {'fk_empreendedor_id_empreendedor': 2}):
            self.assertEqual(self.criar(**extra).status_code, 422, extra)
        with self.sessions() as db:
            self.assertEqual(db.query(PostagemChatDB).count(), 0)
        post = self.criar().json()
        url = f"/postagem/{post['id_post']}"
        for texto in (' ', 'x'*2001):
            self.assertEqual(self.client.post(url+'/comentarios', json={'texto': texto}).status_code, 422)
        self.assertEqual(self.client.patch(url, json={'conteudo_texto': None}).status_code, 422)
        self.assertEqual(self.client.patch(url, json={}).status_code, 422)
        self.assertEqual(self.client.post('/postagem/criar-postagem', headers={'Origin': 'https://invalid.example'}, json={'conteudo_texto': 'Teste'}).status_code, 403)
        self.login(2)
        self.assertEqual(self.client.patch(url, json={'conteudo_texto': 'Outro'}).status_code, 403)
        self.assertEqual(self.client.delete(url).status_code, 403)
        self.login()
        self.assertEqual(self.client.patch(url, json={'conteudo_texto': 'Editado'}).status_code, 200)
        self.assertEqual(self.client.delete(url).status_code, 204)
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_legado_sem_autoria_nao_aparece(self):
        self.login()
        with self.sessions() as db:
            db.add(PostagemChatDB(conteudo_texto='Legado'))
            db.commit()
        self.assertEqual(self.client.get('/postagem').json(), [])

    seed_mentors = fixtures.CompanySessionTests.seed_mentors
    mentor_login = fixtures.CompanySessionTests.mentor_login

    def imagem(self, cor='red'):
        from io import BytesIO
        from PIL import Image
        arquivo = BytesIO()
        Image.new('RGB', (40, 20), cor).save(arquivo, format='PNG')
        return ('imagem.png', arquivo.getvalue(), 'image/png')

    def test_mentor_comunidade_e_isolamento_de_autoria(self):
        from models import MentorAccessDB
        self.seed_mentors()
        self.login()
        empreendedor = self.criar().json()
        self.mentor_login()
        self.assertFalse(self.client.get('/postagem').json()[0]['minha'])
        url = f"/postagem/{empreendedor['id_post']}"
        self.assertEqual(self.client.patch(url, json={'conteudo_texto': 'Outro autor'}).status_code, 403)
        self.assertEqual(self.client.delete(url).status_code, 403)
        resposta = self.client.post(url+'/comentarios', json={'texto': 'Resposta do mentor'})
        self.assertEqual(resposta.status_code, 201)
        self.assertEqual(resposta.json()['autorPapel'], 'mentor')
        mentor = self.criar().json()
        self.assertEqual(mentor['autor_papel'], 'mentor')
        self.assertTrue(mentor['minha'])
        self.assertEqual(mentor['autor_id'], empreendedor['autor_id'])
        self.login()
        url = f"/postagem/{mentor['id_post']}"
        self.assertEqual(self.client.patch(url, json={'conteudo_texto': 'Outro autor'}).status_code, 403)
        self.assertEqual(self.client.delete(url).status_code, 403)
        self.mentor_login()
        self.assertEqual(self.client.patch(url, json={'conteudo_texto': 'Mentor editou'}).status_code, 200)
        with self.sessions() as db:
            db.get(MentorAccessDB, 1).ativo = False
            db.commit()
        self.assertEqual(self.client.get('/postagem').status_code, 403)
        self.assertEqual(self.criar().status_code, 403)

    def test_upload_edicao_remocao_e_exclusao(self):
        from PIL import Image
        from io import BytesIO
        self.login()
        resposta = self.client.post('/postagem/criar-com-imagem', data={'conteudo_texto': 'Com foto'}, files={'imagem': self.imagem()})
        self.assertEqual(resposta.status_code, 201, resposta.text)
        post = resposta.json()
        url = f"/postagem/{post['id_post']}"
        foto_url = post['imagem_upload_url']
        foto = self.client.get(foto_url)
        self.assertEqual(foto.headers['content-type'], 'image/jpeg')
        self.assertEqual(Image.open(BytesIO(foto.content)).format, 'JPEG')
        self.assertEqual(self.client.patch(url, json={'conteudo_texto': 'Texto editado'}).json()['imagem_upload_url'], foto_url)
        self.login(2)
        self.assertEqual(self.client.get(foto_url).status_code, 200)
        self.assertEqual(self.client.patch(url+'/com-imagem', data={'conteudo_texto': 'Indevido'}, files={'imagem': self.imagem()}).status_code, 403)
        self.client.post(url+'/comentarios', json={'texto': 'Comentário'})
        self.login()
        alterada = self.client.patch(url+'/com-imagem', data={'conteudo_texto': 'Nova imagem'}, files={'imagem': self.imagem('blue')})
        self.assertEqual(alterada.status_code, 200, alterada.text)
        self.assertNotEqual(alterada.json()['imagem_upload_url'], foto_url)
        invalida = self.client.patch(url+'/com-imagem', data={'conteudo_texto': 'Não deve salvar'}, files={'imagem': ('x.png', b'nao e imagem', 'image/png')})
        self.assertEqual(invalida.status_code, 422)
        self.assertEqual(self.client.get(url).json()['conteudo_texto'], 'Nova imagem')
        removida = self.client.patch(url, json={'midia_url': None})
        self.assertIsNone(removida.json()['imagem_upload_url'])
        self.assertEqual(self.client.get(foto_url).status_code, 404)
        self.assertEqual(self.client.delete(url).status_code, 204)
        with self.sessions() as db:
            self.assertEqual(db.query(PostagemComentarioDB).count(), 0)
            self.assertEqual(db.query(PostagemChatDB).count(), 0)

    def test_upload_invalido_nao_cria_postagem(self):
        self.login()
        for arquivo, status in [(('x.png', b'fake', 'image/png'), 422),
                                (('x.svg', b'<svg/>', 'image/svg+xml'), 422),
                                (('x.png', b'x'*(5*1024*1024+1), 'image/png'), 413)]:
            resposta = self.client.post('/postagem/criar-com-imagem', data={'conteudo_texto': 'Texto'}, files={'imagem': arquivo})
            self.assertEqual(resposta.status_code, status, resposta.text)
        self.assertEqual(self.client.post('/postagem/criar-com-imagem', data={'conteudo_texto': ' '}, files={'imagem': self.imagem()}).status_code, 422)
        with self.sessions() as db:
            self.assertEqual(db.query(PostagemChatDB).count(), 0)

    def test_mentor_upload_e_imagem_exigem_sessao(self):
        self.seed_mentors()
        self.mentor_login()
        r = self.client.post('/postagem/criar-com-imagem', data={'conteudo_texto': 'Foto do mentor'}, files={'imagem': self.imagem()})
        self.assertEqual(r.status_code, 201, r.text)
        self.assertTrue(r.json()['minha'])
        imagem_url = r.json()['imagem_upload_url']
        self.client.post('/auth/logout')
        self.assertEqual(self.client.get(imagem_url).status_code, 401)
        self.assertEqual(self.client.post('/postagem/criar-com-imagem', data={'conteudo_texto': 'Sem sessão'}, files={'imagem': self.imagem()}).status_code, 401)

    def test_foto_do_autor_e_publica_so_para_comunidade_autenticada(self):
        self.login()
        post = self.criar().json()
        url = f"/postagem/{post['id_post']}/autor/foto"
        self.assertIsNone(post['autor_foto_url'])
        self.assertEqual(self.client.get(url).status_code, 404)
        self.assertEqual(self.client.put('/empreendedor/me/foto', files={'foto': self.imagem()}).status_code, 200)
        foto_original = self.client.get('/empreendedor/me/foto').content
        com_foto = self.client.get('/postagem').json()[0]
        foto_url = com_foto['autor_foto_url']
        self.login(2)
        foto = self.client.get(foto_url)
        self.assertEqual(foto.status_code, 200)
        self.assertEqual(foto.content, foto_original)
        self.assertEqual(foto.headers['content-type'], 'image/jpeg')
        self.assertIn('no-store', foto.headers['cache-control'])
        self.seed_mentors()
        self.mentor_login()
        self.assertEqual(self.client.get(foto_url).content, foto_original)
        mentor_post = self.criar().json()
        self.assertIsNone(mentor_post['autor_foto_url'])
        self.assertEqual(self.client.get(f"/postagem/{mentor_post['id_post']}/autor/foto").status_code, 404)
        self.login()
        self.client.put('/empreendedor/me/foto', files={'foto': self.imagem('blue')})
        self.assertNotEqual(self.client.get(f"/postagem/{post['id_post']}").json()['autor_foto_url'], foto_url)
        self.client.post('/auth/logout')
        self.assertEqual(self.client.get(foto_url).status_code, 401)

    def test_mentor_com_id_zero_pode_ler_editar_comentar_e_excluir(self):
        from main import app
        from routers.postagemRoute import participante
        from models import MentorDB
        with self.sessions() as db:
            db.add(MentorDB(id_mentor=0, nome='Mentor zero', especialidade='Gestão', biografia='Mentor'))
            db.commit()
        app.dependency_overrides[participante] = lambda: ('mentor', 0)
        post = self.criar().json()
        url = f"/postagem/{post['id_post']}"
        self.assertEqual(post['company'], 'Mentor zero')
        self.assertEqual(post['autor_id'], 0)
        self.assertTrue(post['minha'])
        self.assertEqual(self.client.get('/postagem').status_code, 200)
        self.assertEqual(self.client.get(url).status_code, 200)
        self.assertEqual(self.client.get(url+'/autor/foto').status_code, 404)
        comentario = self.client.post(url+'/comentarios', json={'texto': 'Comentário do mentor zero'})
        self.assertEqual(comentario.status_code, 201)
        self.assertEqual(comentario.json()['author'], 'Mentor zero')
        self.assertEqual(self.client.patch(url, json={'conteudo_texto': 'Editado pelo mentor zero'}).status_code, 200)
        self.assertEqual(self.client.delete(url).status_code, 204)

    def test_autor_ausente_nao_derruba_feed(self):
        self.login()
        with self.sessions() as db:
            # Simula registros legados inconsistentes; o SQLite da fixture não impõe FKs.
            post = PostagemChatDB(conteudo_texto='Legado órfão', id_mentor=999)
            db.add(post)
            db.flush()
            db.add(PostagemComentarioDB(id_post=post.id_post, id_empreendedor=999, texto='Comentário órfão'))
            db.commit()
        resposta = self.client.get('/postagem')
        self.assertEqual(resposta.status_code, 200, resposta.text)
        post = resposta.json()[0]
        self.assertEqual(post['company'], 'Autor indisponível')
        self.assertEqual(post['comments'][0]['author'], 'Autor indisponível')
        self.assertFalse(post['minha'])
        self.assertIsNone(post['autor_foto_url'])
