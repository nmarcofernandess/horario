const { FusesPlugin } = require('@electron-forge/plugin-fuses');
const { FuseV1Options, FuseVersion } = require('@electron/fuses');

module.exports = {
  outDir: 'release',
  packagerConfig: {
    asar: true,
    executableName: 'escalaflow',
    ignore: [
      /\/src\//,
      /\/api\//,
    ],
  },
  rebuildConfig: {},
  makers: [
    // Windows: .exe installer
    { name: '@electron-forge/maker-squirrel', config: {} },
    // Mac: DMG (instalador) + ZIP (portátil)
    { name: '@electron-forge/maker-dmg', config: {} },
    { name: '@electron-forge/maker-zip', platforms: ['darwin'] },
    // Linux
    { name: '@electron-forge/maker-deb', config: {} },
    { name: '@electron-forge/maker-rpm', config: {} },
  ],
  plugins: [
    {
      name: '@electron-forge/plugin-auto-unpack-natives',
      config: {},
    },
    new FusesPlugin({
      version: FuseVersion.V1,
      [FuseV1Options.RunAsNode]: false,
      [FuseV1Options.EnableCookieEncryption]: true,
      [FuseV1Options.EnableNodeOptionsEnvironmentVariable]: false,
      [FuseV1Options.EnableNodeCliInspectArguments]: false,
      [FuseV1Options.EnableEmbeddedAsarIntegrityValidation]: true,
      [FuseV1Options.OnlyLoadAppFromAsar]: true,
    }),
  ],
};
