import sounddevice as sd

print("\n=== LISTA DE DISPOSITIVOS ===\n")
print(sd.query_devices())

print("\n=== ESCOLHA SEUS DISPOSITIVOS ===\n")

input_id = int(input("ID do microfone (INPUT): "))
output_id = int(input("ID do fone/caixa (OUTPUT): "))

input_info = sd.query_devices(input_id)
output_info = sd.query_devices(output_id)

print("\n=== RESULTADO ===\n")

print("INPUT:")
print(f"Nome: {input_info['name']}")
print(f"Canais de entrada: {input_info['max_input_channels']}")
print(f"Sample rate padrão: {input_info['default_samplerate']}")

print("\nOUTPUT:")
print(f"Nome: {output_info['name']}")
print(f"Canais de saída: {output_info['max_output_channels']}")
print(f"Sample rate padrão: {output_info['default_samplerate']}")

print("\n=== CONFIG PRONTA PARA USO ===\n")

print(f"AUDIO_INPUT_DEVICE = {input_id}")
print(f"AUDIO_OUTPUT_DEVICE = {output_id}")
print(f"SAMPLE_RATE = {int(input_info['default_samplerate'])}")
print(f"CHANNELS_INPUT = {input_info['max_input_channels']}")
print(f"CHANNELS_OUTPUT = {output_info['max_output_channels']}")