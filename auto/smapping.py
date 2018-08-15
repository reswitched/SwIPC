smapping = {
    # builtins
    '0100000000000000': {
        'fsp-srv': 'nn::fssrv::sf::IFileSystemProxy',
        'fsp-ldr': 'nn::fssrv::sf::IFileSystemProxyForLoader',
        'fsp-pr':  'nn::fssrv::sf::IProgramRegistry',
    },
    '0100000000000001': {
        'ldr:shel': 'nn::ldr::detail::IShellInterface',
        'ldr:pm':   'nn::ldr::detail::IProcessManagerInterface',
        'ldr:dmnt': 'nn::ldr::detail::IDebugMonitorInterface',
    },
    '0100000000000002': {
        'lr':  'nn::lr::ILocationResolverManager',
        'ncm': 'nn::ncm::IContentManager',
    },
    '0100000000000003': {
        'pm:info': 'nn::pm::detail::IInformationInterface',
        'pm:shell': 'nn::pm::detail::IShellInterface',
        'pm:bm':   'nn::pm::detail::IBootModeInterface',
    },
    '0100000000000004': {
        'sm:':  'nn::sm::detail::IUserInterface',
        'sm:m': 'nn::sm::detail::IManagerInterface',
    },
    '0100000000000028': {
        'spl:':  'nn::spl::detail::IGeneralInterface',
        'csrng': 'nn::spl::detail::IRandomInterface',
    },
    # not builtins
	'0100000000000006': {  # usb
		'usb:ds':   'nn::usb::ds::IDsService',
		'usb:hs':   'nn::usb::hs::IClientRootSession',
		'usb:pd':   'nn::usb::pd::detail::IPdManager',
		'usb:pd:c': 'nn::usb::pd::detail::IPdCradleManager',
		'usb:pm':   'nn::usb::pm::IPmService',
	},
	'0100000000000009': {  # settings
		'set':     'nn::settings::ISettingsServer',
		'set:cal': 'nn::settings::IFactorySettingsServer',
		'set:fd':  'nn::settings::IFirmwareDebugSettingsServer',
		'set:sys': 'nn::settings::ISystemSettingsServer',
	},
	'010000000000000A': {  # Bus
		'gpio':    'nn::gpio::IManager',
		'i2c':     'nn::i2c::IManager',
		'i2c:pcv': 'nn::i2c::IManager',
		'pinmux':  'nn::pinmux::IManager',
		'pwm':     'nn::pwm::IManager',
		'sasbus':  'nn::sasbus::IManager',
		'uart':    'nn::uart::IManager',
	},
	'010000000000000B': {  # bluetooth
		'btdrv': 'nn::bluetooth::IBluetoothDriver',
	},
	'010000000000000C': {  # bcat
		'bcat:a':  'nn::bcat::detail::ipc::IServiceCreator',
		'bcat:m':  'nn::bcat::detail::ipc::IServiceCreator',
		'bcat:s':  'nn::bcat::detail::ipc::IServiceCreator',
		'bcat:u':  'nn::bcat::detail::ipc::IServiceCreator',
		'news:a':  'nn::news::detail::ipc::IServiceCreator',
		'news:c':  'nn::news::detail::ipc::IServiceCreator',
		'news:m':  'nn::news::detail::ipc::IServiceCreator',
		'news:p':  'nn::news::detail::ipc::IServiceCreator',
		'news:v':  'nn::news::detail::ipc::IServiceCreator',
		'prepo:a': 'nn::prepo::detail::ipc::IPrepoService',
		'prepo:m': 'nn::prepo::detail::ipc::IPrepoService',
		'prepo:s': 'nn::prepo::detail::ipc::IPrepoService',
		'prepo:u': 'nn::prepo::detail::ipc::IPrepoService',
	},
	'010000000000000E': {  # friends
		'friend:a': 'nn::friends::detail::ipc::IServiceCreator',
		'friend:m': 'nn::friends::detail::ipc::IServiceCreator',
		'friend:s': 'nn::friends::detail::ipc::IServiceCreator',
		'friend:u': 'nn::friends::detail::ipc::IServiceCreator',
		'friend:v': 'nn::friends::detail::ipc::IServiceCreator',
	},
	'010000000000000F': {  # nifm
		'nifm:a': 'nn::nifm::detail::IStaticService',
		'nifm:s': 'nn::nifm::detail::IStaticService',
		'nifm:u': 'nn::nifm::detail::IStaticService',
	},
	'0100000000000010': {  # ptm
		'fan': 'nn::fan::detail::IManager',
		'psm': 'nn::psm::IPsmServer',
		'tc':  'nn::tc::IManager',
		'ts':  'nn::ts::server::IMeasurementServer',
	},
	'0100000000000012': {  # bsdsocket
		'bsd:s':    'nn::socket::sf::IClient', # ?
		'bsd:u':    'nn::socket::sf::IClient', # ?
		'bsdcfg':   'nn::bsdsocket::cfg::ServerInterface',
		'ethc:c':   'nn::eth::sf::IEthInterface',
		'ethc:i':   'nn::eth::sf::IEthInterfaceGroup',
		'nsd:a':    'nn::nsd::detail::IManager', # ?
		'nsd:u':    'nn::nsd::detail::IManager', # ?
		'sfdnsres': 'nn::socket::resolver::IResolver',
	},
	'0100000000000013': {  # hid
		'ahid:cd':  'nn::ahid::IServerSession', # ?
		'ahid:hdr': 'nn::ahid::hdr::ISession',  # ?
		'hid':      'nn::hid::IHidServer',
		'hid:dbg':  'nn::hid::IHidDebugServer',
		'hid:sys':  'nn::hid::IHidSystemServer',
		'hid:tmp':  'nn::hid::IHidTemporaryServer',
		'irs':      'nn::irsensor::IIrSensorServer',
		'irs:sys':  'nn::irsensor::IIrSensorSystemServer',
		'xcd:sys':  'nn::xcd::detail::ISystemServer',
	},
	'0100000000000014': {  # audio
		'audctl':   'nn::audioctrl::detail::IAudioController',
		'audin:a':  'nn::audio::detail::IAudioInManagerForApplet',
		'audin:d':  'nn::audio::detail::IAudioInManagerForDebugger',
		'audin:u':  'nn::audio::detail::IAudioInManager',
		'audout:a': 'nn::audio::detail::IAudioOutManagerForApplet',
		'audout:d': 'nn::audio::detail::IAudioOutManagerForDebugger',
		'audout:u': 'nn::audio::detail::IAudioOutManager',
		'audrec:a': 'nn::audio::detail::IFinalOutputRecorderManagerForApplet',
		'audrec:d': 'nn::audio::detail::IFinalOutputRecorderManagerForDebugger',
		'audrec:u': 'nn::audio::detail::IFinalOutputRecorderManager',
		'audren:a': 'nn::audio::detail::IAudioRendererManagerForApplet',
		'audren:d': 'nn::audio::detail::IAudioRendererManagerForDebugger',
		'audren:u': 'nn::audio::detail::IAudioRendererManager',
		'hwopus':   'nn::codec::detail::IHardwareOpusDecoderManager',
	},
	'0100000000000015': {  # LogManager.Prod
		'lm': 'nn::lm::ILogService',
	},
	'0100000000000016': {  # wlan
		'wlan:inf': 'nn::wlan::detail::IInfraManager',
		'wlan:lcl': 'nn::wlan::detail::ILocalManager',
		'wlan:lg':  'nn::wlan::detail::ILocalGetFrame',
		'wlan:lga': 'nn::wlan::detail::ILocalGetActionFrame',
		'wlan:soc': 'nn::wlan::detail::ISocketManager',
		'wlan:sg':  'nn::wlan::detail::ISocketGetFrame',
	},
	'0100000000000018': {  # ldn
		'ldn:m': 'nn::ldn::detail::IMonitorServiceCreator',
		'ldn:s': 'nn::ldn::detail::ISystemServiceCreator',
		'ldn:u': 'nn::ldn::detail::IUserServiceCreator',
	},
	'0100000000000019': {  # nvservices
		'nvdrv':    'nns::nvdrv::INvDrvServices',
		'nvdrv:a':  'nns::nvdrv::INvDrvServices',
		'nvdrv:s':  'nns::nvdrv::INvDrvServices',
		'nvdrv:t':  'nns::nvdrv::INvDrvServices',
		'nvdrvdbg': 'nns::nvdrv::INvDrvDebugFSServices',
		'nvgem:c':  'nv::gemcontrol::INvGemControl',
		'nvgem:cd': 'nv::gemcoredump::INvGemCoreDump',
	},
	'010000000000001A': {  # pcv
		'bpc':     'nn::bpc::IBoardPowerControlManager',
		'bpc:r':   'nn::bpc::IRtcManager',
		'pcv':     'nn::pcv::detail::IPcvService',
		'pcv:arb': 'nn::pcv::IArbitrationManager',
		'pcv:imm': 'nn::pcv::IImmediateManager',
		'time:u':  'nn::timesrv::detail::service::IStaticService',
		'time:a':  'nn::timesrv::detail::service::IStaticService',
		'time:s':  'nn::timesrv::detail::service::IStaticService',
		'time:r':  'nn::timesrv::detail::service::IStaticService',
	},
	'010000000000001B': {  # ppc
		'apm':     'nn::apm::IManager',
		'apm:p':   'nn::apm::IManagerPrivileged',
		'apm:sys': 'nn::apm::ISystemManager',
		'fgm:0':   'nn::fgm::sf::ISession',
		'fgm':     'nn::fgm::sf::ISession',
		'fgm:9':   'nn::fgm::sf::ISession', # no nn::fgm::sf::IDebugger ?
	},
	'010000000000001C': {  # nvnflinger
		'dispdrv': 'nns::hosbinder::IHOSBinderDriver',
	},
	'010000000000001D': {  # pcie.withoutHb
		'pcie': 'nn::pcie::detail::IManager',
	},
	'010000000000001E': {  # account
		'acc:aa': 'nn::account::IBaasAccessTokenAccessor', # ?
		'acc:su': 'nn::account::IAccountServiceForAdministrator', # ?
		'acc:u1': 'nn::account::IAccountServiceForSystemService', # ?
		'acc:u0': 'nn::account::IAccountServiceForApplication', # ?
	},
	'010000000000001F': {  # ns
		'aoc:u':    'nn::aocsrv::detail::IAddOnContentManager',
		'ns:am2':   'nn::ns::detail::IServiceGetterInterface',
		'ns:dev':   'nn::ns::detail::IDevelopInterface',
		'ns:ec':    'nn::ns::detail::IServiceGetterInterface',
		'ns:rid':   'nn::ns::detail::IServiceGetterInterface',
		'ns:rt':    'nn::ns::detail::IServiceGetterInterface',
		'ns:su':    'nn::ns::detail::ISystemUpdateInterface',
		'ns:vm':    'nn::ns::detail::IVulnerabilityManagerInterface',
		'ns:web':   'nn::ns::detail::IServiceGetterInterface',
		'ovln:rcv': 'nn::ovln::IReceiverService',
		'ovln:snd': 'nn::ovln::ISenderService',
	},
	'0100000000000020': {  # nfc
		'nfc:am':   'nn::nfc::am::detail::IAmManager',
		'nfc:mf:u': 'nn::nfc::mifare::detail::IUserManager',
		'nfc:sys':  'nn::nfc::detail::ISystemManager',
		'nfc:user': 'nn::nfc::detail::IUserManager',
		'nfp:dbg':  'nn::nfp::detail::IDebugManager',
		'nfp:sys':  'nn::nfp::detail::ISystemManager',
		'nfp:user': 'nn::nfp::detail::IUserManager',
	},
	'0100000000000021': {  # psc
		'psc:c': 'nn::psc::sf::IPmControl', # ?
		'psc:m': 'nn::psc::sf::IPmService', # ?
	},
	'0100000000000022': {  # capsrv
		'caps:a': 'nn::capsrv::sf::IAlbumAccessorService',
		'caps:c': 'nn::capsrv::sf::IAlbumControlService',
	},
	'0100000000000023': {  # am
		'appletAE': 'nn::am::service::IAllSystemAppletProxiesService',
		'appletOE': 'nn::am::service::IApplicationProxyService',
		'idle:sys': 'nn::idle::detail::IPolicyManagerSystem',
		'omm':      'nn::omm::detail::IOperationModeManager',
		'spsm':     'nn::spsm::detail::IPowerStateInterface',
	},
	'0100000000000024': {  # ssl
		'ssl': 'nn::ssl::sf::ISslService', # ?
	},
	'0100000000000025': {  # nim
		'nim':     'nn::nim::detail::INetworkInstallManager',
		'nim:shp': 'nn::nim::detail::IShopServiceManager',
		'ntc':     'nn::ntc::detail::service::IStaticService',
	},
	'0100000000000029': {  # lbl
		'lbl': 'nn::lbl::detail::ILblController',
	},
	'010000000000002A': {  # btm
		'btm':     'nn::btm::IBtm',
		'btm:dbg': 'nn::btm::IBtmDebug',
		'btm:sys': 'nn::btm::IBtmSystem',
	},
	'010000000000002B': {  # erpt
		'erpt:c': 'nn::erpt::sf::IContext',
		'erpt:r': 'nn::erpt::sf::ISession',
	},
	'010000000000002D': {  # vi
		'caps:sc': 'nn::capsrv::sf::IScreenShotControlService',
		'caps:ss': 'nn::capsrv::sf::IScreenShotService',
		'caps:su': 'nn::capsrv::sf::IScreenShotApplicationService',
		'cec-mgr': 'nn::cec::ICecManager',
		'mm:u':    'nn::mmnv::IRequest',
		'vi:m':    'nn::visrv::sf::IManagerRootService',
		'vi:s':    'nn::visrv::sf::ISystemRootService',
		'vi:u':    'nn::visrv::sf::IApplicationRootService',
	},
	'010000000000002E': {  # pctl
		'pctl':   'nn::pctl::detail::ipc::IParentalControlServiceFactory',
		'pctl:a': 'nn::pctl::detail::ipc::IParentalControlServiceFactory',
		'pctl:r': 'nn::pctl::detail::ipc::IParentalControlServiceFactory',
		'pctl:s': 'nn::pctl::detail::ipc::IParentalControlServiceFactory',
	},
	'010000000000002F': {  # npns
		'npns:s': 'nn::npns::INpnsSystem',
		'npns:u': 'nn::npns::INpnsUser',
	},
	'0100000000000030': {  # eupld
		'eupld:c': 'nn::eupld::sf::IControl',
		'eupld:r': 'nn::eupld::sf::IRequest',
	},
	'0100000000000031': {  # glue
		'arp:r':   'nn::arp::detail::IReader',
		'arp:w':   'nn::arp::detail::IWriter',
		'bgtc:sc': 'nn::bgtc::IStateControlService',
		'bgtc:t':  'nn::bgtc::ITaskService',
	},
	'0100000000000033': {  # es
		'es': 'nn::es::IETicketService',
	},
	'0100000000000034': {  # fatal
		'fatal:p': 'nn::fatalsrv::IPrivateService',
		'fatal:u': 'nn::fatalsrv::IService',
	},
	'0100000000000037': {  # ro
		'ldr:ro':  'nn::ro::detail::IRoInterface',
		'ro:dmnt': 'nn::ro::detail::IDebugMonitorInterface', # ?
	},
	'0100000000000039': {  # sdb
		'mii:e':    'nn::mii::detail::IStaticService',
		'mii:u':    'nn::mii::detail::IStaticService',
		'pdm:ntfy': 'nn::pdm::detail::INotifyService',
		'pdm:qry':  'nn::pdm::detail::IQueryService',
		'pl:u':     'nn::pl::detail::ISharedFontManager',
	},
}
