import mido

def capture_input():
    # List all available MIDI input ports
    input_ports = mido.get_input_names()
    print("Available MIDI input ports:")
    for port in input_ports:
        print(port)

    # Select the Akai MPKmini input port (you can also adjust this based on the list above)
    input_port_name = next(port for port in input_ports if 'MPKmini' in port)

    # Open the input port
    with mido.open_input(input_port_name) as inport:
        print(f"Listening on {input_port_name}...")

        # Start capturing MIDI messages
        for msg in inport:
            print(msg)
