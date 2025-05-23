import endaq
import traceback

def analyze_endaq(file_path):
    try:
        print(f"Opening IDE file: {file_path}")
        # Get the document and channels
        doc = endaq.ide.get_doc(file_path)
        print("Successfully loaded IDE document")

        # Get the channels
        print("Getting acceleration channels...")
        channels = endaq.ide.get_channels(doc, 'acceleration', subchannels=False)
        print(f"Found {len(channels)} acceleration channels")

        # Get the data for the 25g and 40g channels
        print("Processing 25g channel...")
        pd_25g = endaq.ide.to_pandas(channels[0])
        
        skip_40g = False
        try:
            print("Processing 40g channel...")
            pd_40g = endaq.ide.to_pandas(channels[1])
        except IndexError:
            print("No 40g channel found, skipping...")
            skip_40g = True

        # Calculate the PSD for the 25g and 40g channels
        print("Calculating PSD for 25g channel...")
        psd_25g = endaq.calc.psd.welch(pd_25g, bin_width=0.25)
        
        if not skip_40g:
            print("Calculating PSD for 40g channel...")
            psd_40g = endaq.calc.psd.welch(pd_40g, bin_width=0.25)
        else:
            psd_40g = None

        # Calculate the VC curves for the 25g and 40g channels
        print("Calculating VC curves for 25g channel...")
        vc_25g = endaq.calc.psd.vc_curves(psd_25g, fstart=1.0, octave_bins=3)
        
        if not skip_40g:
            print("Calculating VC curves for 40g channel...")
            vc_40g = endaq.calc.psd.vc_curves(psd_40g, fstart=1.0, octave_bins=3)
        else:
            vc_40g = None

        print("Analysis complete")
        # Return the data for the 25g and 40g channels
        if skip_40g:
            return vc_25g
        else:
            return vc_25g, vc_40g
            
    except Exception as e:
        print(f"Error in analyze_endaq: {str(e)}")
        print("Traceback:")
        traceback.print_exc()
        raise