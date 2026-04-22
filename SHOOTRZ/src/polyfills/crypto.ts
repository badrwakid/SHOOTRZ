import * as ExpoCrypto from 'expo-crypto';

type ArrayBufferInput = ArrayBuffer | ArrayBufferView | string;

// Type definitions for Web Crypto API polyfill
type AlgorithmIdentifier = string | { name: string };

const toUint8Array = (input: ArrayBufferInput): Uint8Array => {
  if (ArrayBuffer.isView(input)) {
    const view = input as ArrayBufferView;
    return new Uint8Array(view.buffer, view.byteOffset, view.byteLength);
  }

  if (input instanceof ArrayBuffer) {
    return new Uint8Array(input);
  }

  const encoder = typeof TextEncoder !== 'undefined' ? new TextEncoder() : null;
  if (encoder) {
    return encoder.encode(String(input));
  }

  const str = String(input);
  const buffer = new Uint8Array(str.length);
  for (let i = 0; i < str.length; i += 1) {
    buffer[i] = str.charCodeAt(i) & 0xff;
  }
  return buffer;
};

const unsupported = (name: string) => () =>
  Promise.reject(new Error(`crypto.subtle.${name} is not supported in this environment`));

const ensureCrypto = () => {
  const globalCrypto = (globalThis.crypto as any) ?? ((globalThis.crypto = {} as any), globalThis.crypto);

  if (typeof globalCrypto.getRandomValues !== 'function') {
    globalCrypto.getRandomValues = <T extends ArrayBufferView>(array: T): T => {
      const randomBytes = ExpoCrypto.getRandomBytes(array.byteLength);
      const randomView = new Uint8Array(array.buffer, array.byteOffset, array.byteLength);
      randomView.set(randomBytes);
      return array;
    };
  }

  if (!globalCrypto.subtle) {
    const subtle = {
      async digest(algorithm: AlgorithmIdentifier, data: ArrayBufferInput) {
        const algo = typeof algorithm === 'string' ? algorithm : algorithm?.name;
        if (!algo || algo.toUpperCase() !== 'SHA-256') {
          throw new Error(`Algorithm not supported: ${algo}`);
        }
        const bytes = toUint8Array(data);
        // Create a new Uint8Array with a proper ArrayBuffer (not SharedArrayBuffer)
        const buffer = new Uint8Array(bytes.length);
        buffer.set(bytes);
        const result = await ExpoCrypto.digest(ExpoCrypto.CryptoDigestAlgorithm.SHA256, buffer);
        return result;
      },
      encrypt: unsupported('encrypt'),
      decrypt: unsupported('decrypt'),
      sign: unsupported('sign'),
      verify: unsupported('verify'),
      deriveBits: unsupported('deriveBits'),
      deriveKey: unsupported('deriveKey'),
      generateKey: unsupported('generateKey'),
      importKey: unsupported('importKey'),
      exportKey: unsupported('exportKey'),
      wrapKey: unsupported('wrapKey'),
      unwrapKey: unsupported('unwrapKey'),
    };

    (globalCrypto as any).subtle = subtle;
  }
};

ensureCrypto();

