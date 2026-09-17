import discord
from discord.ext import commands
from discord import Embed
from discord.utils import get
import aiohttp
from discord import app_commands
import discord
import json
import os
from discord import Poll

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.members = True

lang_file = "lang.json"
server_lucky_ids = [1395862013082865775, 1477072294110171256, 1514583484562145340]

bot = commands.Bot(command_prefix="!", intents=intents)

# Roles
ROL_SI_ES = "Si"
ROL_NOSE = "?"
ROL_SI_EN = "Yes"
ROL_NO = "No"
mensaje_scrim_id = None

#------Version-------
@bot.command()
async def version(ctx):
    await ctx.send(t("Version: 1.3.5"))
#-----------------Idioma---------------- 
# Textos multi-idioma
TEXTOS = {
    "es": {
        "rol_creado": "Rol creado",
        "nadie_si": "Nadie dijo que sí",
        "nadie_no": "Nadie dijo que no",
        "scrim_pregunta": "¿Podéis hoy scrim?",
        "scrim_comienza": "La scrim empieza en poco:",
        "reseteando": "Reseteando...",
        "reseteandof": "Reseteando",
        "no_roles": "No se encontraron los roles 'Si' o 'No'",
        "info": "Soy un bot creado por Nube para organizar scrims de OW, Nube es tonto, así que no te tomes muy en serio si el bot va bien o no\nhttps://www.twitch.tv/nubevt\nContacto: nubee.",
        "idioma_cambiado": "Idioma cambiado a Español",
        "idioma_error": "Idioma no soportado, usa 'es' o 'en'",
        "rolrecuerdo": "Recuerda que el rol del bot tiene que tener permiso para cambiar los roles y tiene que estar por encima del rol de los jugadores al igual que el rol: Si, No y '?', para asegurar un buen funcionamineto ^^"
    },
    "en": {
        "rol_creado": "Role created",
        "nadie_si": "Nobody said yes",
        "nadie_no": "Nobody said no",
        "scrim_pregunta": "Can you scrim today?",
        "scrim_comienza": "The scrim will start soon:",
        "reseteando": "Resetting...",
        "reseteandof": "Restart complete",
        "no_roles": "Roles 'Yes' or 'No' not found",
        "info": "I'm a bot made by Nube to organize OW scrims. Nube is silly, so don't take it too seriously if the bot works well or not.\nhttps://www.twitch.tv/nubevt\nContact: nubee.",
        "idioma_cambiado": "Language changed to English",
        "idioma_error": "Unsupported language, use 'es' or 'en'",
        "rolrecuerdo": "Remember that the bot's role must have permission to change roles and must be above the players' roles, as well as the 'Yes', 'No', and '?' roles, to ensure proper functioning ^^"
    }
}
idiomas_servidor = {} 

def load_languages():
    global idiomas_servidor
    if os.path.exists(lang_file):
        with open(lang_file, "r", encoding="utf-8") as f:
            idiomas_servidor = json.load(f)
            # convertir keys a int
            idiomas_servidor = {int(k): v for k, v in idiomas_servidor.items()}
    else:
        idiomas_servidor = {}

def save_languages():
    with open(lang_file, "w", encoding="utf-8") as f:
        json.dump(idiomas_servidor, f, indent=4)

#--------------------FUNCIONES-----------------------
def t(key, guild_id=None):
    lang = "en"
    if guild_id and guild_id in idiomas_servidor:
        lang = idiomas_servidor[guild_id]
    return TEXTOS[lang].get(key, key)

def get_rol_si(guild_id=None):
    return ROL_SI_EN if idiomas_servidor.get(guild_id, "en") == "en" else ROL_SI_ES

def get_rol_no(guild_id=None):
    return ROL_NO

def get_rol_nose(guild_id=None):
    return ROL_NOSE

#--------------------EVENTOS-----------------------
@bot.event
async def on_ready():
    load_languages()
    print(f"Bot listo! Conectado como {bot.user}")
    try:
        synced = await bot.tree.sync()
        print("Slash commands sincronizados")
    except Exception as e:
        print(e)

@bot.event
async def on_guild_join(guild):
    if guild.id not in idiomas_servidor:
        idiomas_servidor[guild.id] = "en"
        save_languages()

#--------------------CREAR ROLES-----------------------
@bot.command(name="rol")
@commands.has_permissions(administrator=True)
async def rol(ctx):
    guild = ctx.guild
    rol_si_nombre = get_rol_si(ctx.guild.id) 
    rol_no_nombre = ROL_NO 
    rol_nose_nombre = ROL_NOSE                  

    try:
        # Crear roles
        rol_si = await guild.create_role(name=rol_si_nombre, colour=discord.Colour.green())
        rol_no = await guild.create_role(name=rol_no_nombre, colour=discord.Colour.red())
        rol_nose = await guild.create_role(name=rol_nose_nombre, colour=discord.Colour.yellow())

        # Obtener el rol más alto del bot
        bot_rol = guild.me.top_role

        # Mover los roles recién creados **justo debajo del bot**, en orden descendente
        
        await rol_si.edit(position=bot_rol.position - 1)
        await rol_nose.edit(position=bot_rol.position - 2)
        await rol_no.edit(position=bot_rol.position - 3)

        # Mensajes multilenguaje
        await ctx.send(t("rol_creado", ctx.guild.id))
        await ctx.send(t("rolrecuerdo", ctx.guild.id))

    except Exception as e:
        print(e)
        await ctx.send("Error al crear los roles, no permission")

    if isinstance(error, commands.MissingPermissions):
        await ctx.send("Error: I don't have permission to do that.")
        return
    
#----------------mix-------------------

@bot.command()
async def mix(ctx, *, mensaje_opcional: str = None):

    embed = Embed(
        title="",
        description="Quereis mix hoy?",
        color=discord.Color.blue()
    )

    mensaje = await ctx.send(embed=embed)

    # Añadir reacciones
    await mensaje.add_reaction("✅")
    await mensaje.add_reaction("➖")
    await mensaje.add_reaction("❌")

@bot.event
async def on_raw_reaction_add(payload):
    global mensaje_scrim_id
    if payload.user_id == bot.user.id:
        return
    if mensaje_scrim_id is None or payload.message_id != mensaje_scrim_id:
        return

    guild = bot.get_guild(payload.guild_id)
    if guild is None:
        return
    member = guild.get_member(payload.user_id)
    if member is None:
        return

    rol_si = get(guild.roles, name=get_rol_si(guild.id))
    rol_no = get(guild.roles, name=ROL_NO)
    rol_nose = get(guild.roles, name=ROL_NOSE)

    if rol_si is None or rol_no is None or rol_nose is None:
        print(t("no_roles", guild.id))
        return

    if payload.emoji.name == "✅":
        await member.add_roles(rol_si)
        # Eliminar los otros dos roles si los tiene
        await member.remove_roles(*[r for r in [rol_no, rol_nose] if r in member.roles])
        print(f"Asignado rol SI a {member}")

    elif payload.emoji.name == "❌":
        await member.add_roles(rol_no)
        await member.remove_roles(*[r for r in [rol_si, rol_nose] if r in member.roles])
        print(f"Asignado rol NO a {member}")

    elif payload.emoji.name == "➖":
        await member.add_roles(rol_nose)
        await member.remove_roles(*[r for r in [rol_si, rol_no] if r in member.roles])
        print(f"Rol Nose asignado a {member}")

#------------Scrim Hora-------------    
@bot.command()
async def hour(ctx):

    msg_hour = """
    1. 20:00 / 22:00 \n
    2. 21:00 / 23:00 \n
    """

    embed = Embed(
        title="",
        description=msg_hour,
        color=discord.Color.blue()
    )

    msg = await ctx.send(embed=embed)

    await msg.add_reaction("1️⃣")
    await msg.add_reaction("2️⃣")
    
#-----------Confirmacion de horas--------------

#-----------------------------------

@bot.command(name="roldel")
@commands.has_permissions(administrator=True)
async def roldel(ctx):
    guild = ctx.guild

    # Lista de todos los nombres de roles que quieres borrar
    roles_a_borrar = [
        ROL_SI_ES,
        ROL_SI_EN,
        ROL_NO,
        ROL_NOSE
    ]

    borrados = []

    for nombre in roles_a_borrar:
        rol = discord.utils.get(guild.roles, name=nombre)
        if rol:
            await rol.delete(reason="Borrado de roles del bot")
            borrados.append(nombre)

    if borrados:
        await ctx.send(f"Roles deleted: {', '.join(borrados)}")
    else:
        await ctx.send("No roles to delete")
    
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("Error: I don't have permission to do that.")
        return

#--------------------COMPROBAR ROLES | SI y NO -----------------------
@bot.command(name="si")
async def QuienSi(ctx):
    rol = get(ctx.guild.roles, name=get_rol_si(ctx.guild.id))
    if rol:
        if rol.members:
            lista = [m.display_name for m in rol.members]
            await ctx.send(f"{t('scrim_comienza', ctx.guild.id)}\n" + "\n".join(lista))
        else:
            await ctx.send(t("nadie_si", ctx.guild.id))
    else:
        await ctx.send(f"rol no encontrado '{get_rol_si(ctx.guild.id)}'")

@bot.command(name="yes")
async def QuienYes(ctx):
    rol = get(ctx.guild.roles, name=get_rol_si(ctx.guild.id))
    if rol:
        if rol.members:
            lista = [m.display_name for m in rol.members]
            await ctx.send(f"{t('scrim_comienza', ctx.guild.id)}\n" + "\n".join(lista))
        else:
            await ctx.send(t("nadie_si", ctx.guild.id))
    else:
        await ctx.send(f"rol no encontrado '{get_rol_si(ctx.guild.id)}'")

@bot.command(name="no")
async def QuienNo(ctx):
    rol = get(ctx.guild.roles, name=ROL_NO)
    if rol:
        if rol.members:
            lista = [m.display_name for m in rol.members]
            await ctx.send(f"{t('Estos son los que no:', ctx.guild.id)}\n" + "\n".join(lista))
        else:
            await ctx.send(t("Estos son los que no:", ctx.guild.id))
    else:
        await ctx.send(f"rol no encontrado '{ROL_NO}'")

#--------------------PING A LOS QUE DIJERON SI-----------------------
@bot.command()
async def start(ctx):
    rol = get(ctx.guild.roles, name=get_rol_si(ctx.guild.id))
    if rol and rol.members:
        lista = [m.mention for m in rol.members]
        await ctx.send(t("scrim_comienza", ctx.guild.id) + "\n" + "\n".join(lista))
    else:
        await ctx.send(t("nadie_si", ctx.guild.id))

#--------------------SCRIM REACTIONS----------------------- #Para que el Bot reaccione al !scrim
@bot.command()
async def scrim(ctx, *, mensaje_opcional: str = None):
    """
    Envía un embed para la scrim. 
    Si se pasa texto después de !scrim, se usa ese mensaje.
    Si no, usa el texto por defecto del idioma.
    """
    global mensaje_scrim_id

    # Usar texto por defecto si no se pasa ninguno
    if mensaje_opcional is None:
        mensaje_opcional = t("scrim_pregunta", ctx.guild.id)

    embed = Embed(
        title="",
        description=mensaje_opcional,
        color=discord.Color.blue()
    )

    mensaje = await ctx.send(embed=embed)

    # Añadir reacciones
    await mensaje.add_reaction("✅")
    await mensaje.add_reaction("➖")
    await mensaje.add_reaction("❌")

    mensaje_scrim_id = mensaje.id

@bot.event
async def on_raw_reaction_add(payload):
    global mensaje_scrim_id
    if payload.user_id == bot.user.id:
        return
    if mensaje_scrim_id is None or payload.message_id != mensaje_scrim_id:
        return

    guild = bot.get_guild(payload.guild_id)
    if guild is None:
        return
    member = guild.get_member(payload.user_id)
    if member is None:
        return

    rol_si = get(guild.roles, name=get_rol_si(guild.id))
    rol_no = get(guild.roles, name=ROL_NO)
    rol_nose = get(guild.roles, name=ROL_NOSE)

    if rol_si is None or rol_no is None or rol_nose is None:
        print(t("no_roles", guild.id))
        return

    if payload.emoji.name == "✅":
        await member.add_roles(rol_si)
        # Eliminar los otros dos roles si los tiene
        await member.remove_roles(*[r for r in [rol_no, rol_nose] if r in member.roles])
        print(f"Asignado rol SI a {member}")

    elif payload.emoji.name == "❌":
        await member.add_roles(rol_no)
        await member.remove_roles(*[r for r in [rol_si, rol_nose] if r in member.roles])
        print(f"Asignado rol NO a {member}")

    elif payload.emoji.name == "➖":
        await member.add_roles(rol_nose)
        await member.remove_roles(*[r for r in [rol_si, rol_no] if r in member.roles])
        print(f"Rol Nose asignado a {member}")

#--------------------RESET ROLES-----------------------
@bot.command()
async def resett(ctx):
    guild = ctx.guild

    rol_si = get(guild.roles, name=get_rol_si(guild.id))
    rol_no = get(guild.roles, name=ROL_NO)
    rol_nose = get(guild.roles, name=ROL_NOSE)

    if rol_si is None or rol_no is None or rol_nose is None:
        await ctx.send(t("no_roles", ctx.guild.id))
        return

    # Lista de nombres posibles para rol de jugadores
    nombres_jugadores = ["Player", "player", "Jugador", "jugador", "Jugadores", "jugadores", "Assistant_Coach", "Coach", "Ringer","Assistant Coach"]

    # Buscar rol de jugador
    rol_jugadores = None
    for nombre in nombres_jugadores:
        rol_jugadores = get(guild.roles, name=nombre)
        if rol_jugadores:
            break

    await ctx.send(t("reseteando", ctx.guild.id))

    if rol_jugadores:
        # Solo eliminar roles de los miembros que tengan el rol de jugador
        miembros = [m for m in guild.members if rol_jugadores in m.roles and not m.bot]
    else:
        # No existe rol de jugador, eliminar de todos
        miembros = [m for m in guild.members if not m.bot]

    for member in miembros:
        await member.remove_roles(rol_si, rol_no, rol_nose)

    await ctx.send(t("reseteandof", ctx.guild.id))  

@bot.command()
async def reset(ctx):
    rol_si = get(ctx.guild.roles, name=get_rol_si(ctx.guild.id))
    rol_no = get(ctx.guild.roles, name=ROL_NO)
    rol_nose = get(ctx.guild.roles, name=ROL_NOSE)
    if rol_si is None or rol_no is None:
        await ctx.send(t("no_roles", ctx.guild.id))
        return
    for member in ctx.guild.members:
        if member.bot:
            continue
        await member.remove_roles(rol_si, rol_no, rol_nose)
    await ctx.send(t("reseteando", ctx.guild.id))

#--------------------INFO Y COMANDOS-----------------------
@bot.command()
async def info(ctx):
    await ctx.send(t("info", ctx.guild.id))

@bot.command()
async def comands(ctx):
    lang = idiomas_servidor.get(ctx.guild.id, "en")  
    if lang == "es":
        msg = (
            "--------------------Comandos---------------------\n"   
            "**Porfavor para que el bot no tenga fallos, asegurate que su rol (Scrim Cat) esta arriba de el de los jugadores y tiene permisos para crear, eliminar y poner roles**"
            "\n"
            "**!rol**: Crea los roles Si y No" "**  <-- Usa este comando primero**\n"
            "**!info**: Información sobre el bot\n"
            "**!scrim**: Pregunta si pueden scrim (Si pones !scrim [Texto EJ: Scrim a las 20:00], el bot lo pondra tambien)\n"
            "**!reset**: Resetea el 'scrim'\n"
            f"**!si**: Muestra quien puede la scrim ({get_rol_si(ctx.guild.id)})\n"
            f"**!no**: Muestra quien no puede ({get_rol_no(ctx.guild.id)})\n"
            "**!start**: Ping a los que dijeron que sí\n"
            "**!bug**: Reporta todo bug que encuentres \n"
            "**!template**: If you need a server template \n"
            "**To use it in english:** !setlang en\n"
            "\n"
            "Para cuaquier tipo de error: \n"
            "Contact: nubee."
        )
    else:
        msg = (
            "--------------------Commands---------------------\n"
            "**Please ensure that the bot's role (Scrim Cat) is above the players' roles and has permissions to create, delete, and assign roles to prevent errors**"
            "\n"
            "**!rol**: Create the roles Yes and No" "**  <-- Use this comand first**\n"
            "**!info**: Info about the bot\n"
            "**!scrim**: Ask if they can scrim (If you type !scrim [Text EX: Scrim at 8:00 PM], the bot will do it too)\n"
            "**!reset**: Reset the 'scrim'\n"
            f"**!yes**: See who can scrim ({get_rol_si(ctx.guild.id)})\n"
            f"**!no**: See who cannot ({get_rol_no(ctx.guild.id)})\n"
            "**!start**: Ping all members who said yes\n"
            "**!bug**: Report bugs \n"
            "**!template**: If you need a template for a ser \n"
            "**Para usarlo en español:** !setlang es"
            "\n"
            "For any type of error: \n" 
            "Contact: nubee."
        )
    await ctx.send(msg)
#----------------------------Plantilla----------------------
@bot.command()
async def template(ctx):
    await ctx.send("https://discord.new/e787WxPhQQfR")

#---------------------------MSG comands--------------------- #Full coña comandos
canal_dest = 1395862014177574956

@bot.command()
async def msgs(ctx, *, msgs: str = None):
    canal_id = 1395862014177574956
    canal = bot.get_channel(canal_id)

    if canal is None:
        await ctx.send("No channel found")
        return

    if msgs is None:
        await ctx.send("Put a msg to send")
        return
    
    await canal.send(msgs)

@bot.command()
async def msgg(ctx, *, msgg: str = None):
    canal_id = 1395862014177574954
    canal = bot.get_channel(canal_id)
    nubeid = 323827010348515328

    if ctx.author.id == nubeid:

        if canal is None:
            await ctx.send("No channel found")
            return

        if msgg is None:
            await ctx.send("Put a msg to send")
            return
        
        await canal.send(msgg)

    else:
        ctx.send("You dont have acccess to use this command")

@bot.command()
async def msgc(ctx, canal_id: int, *, msgc: str = None):

    canal = bot.get_channel(canal_id)

    if canal is None:
        await ctx.send("No pude encontrar el canal. Revisa la ID.")
        return

    if msgc is None:
        await ctx.send("Put a msg to send")
        return

    await canal.send(msgc)
    await ctx.send(f"Msg send to: {canal.mention}")

@bot.command()
async def bug(ctx, *, bug: str = None):
    canal_id = 1462561920350683228
    canal = bot.get_channel(canal_id)

    if canal is None:
        await ctx.send("")
        return

    if bug is None:
        await ctx.send("Put a msg to send")
        return
    
    await canal.send(bug)
    await ctx.send(f"Bug have been reported, TY ^^")

# ---------------------------------------------------------------------------------------------------- FUNCIONES ----------------------------------------------------------------------------------------------------------------------

#--------------------CAMBIO DE IDIOMA-----------------------
@bot.command()
async def setlang(ctx, idioma: str):
    idioma = idioma.lower()
    if idioma not in ["es", "en"]:
        await ctx.send(t("idioma_error", ctx.guild.id))
        return

    idiomas_servidor[ctx.guild.id] = idioma
    save_languages()

    await ctx.send(t("idioma_cambiado", ctx.guild.id))

bot.run("Token")  
